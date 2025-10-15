"""
State Manager

Manages VM instance state using SQLite backend with XDG directory compliance.
Provides persistent storage for VM definitions, process tracking, and session management.

"""

# NOTE: Current name vs id design is optimal: UUID primary keys for internal
# use,
# human-readable names for CLI. This provides both uniqueness and usability.
import json
import os
import re
import shutil
import sqlite3
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

from benedict import benedict

from .constants import Database as DBConstants
from .constants import Intervals, Retries, Timeouts
from .exceptions import DatabaseError, DatabaseLockError, StateError
from .logger import LOG

# Optional dependency - imported inline with fallback
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    # psutil is optional - only needed for enhanced process validation
    # Install with: pip install psutil
    # Without psutil, basic PID tracking still works but lacks ownership checks


# Legacy exception alias (backward compatibility)
StateManagerError = StateError


# Database migration registry
# Add new migrations here as functions that take a sqlite3.Connection parameter
# Example:
# def migrate_v1_to_v2(conn: sqlite3.Connection) -> None:
#     """Add new column to vm_instances table."""
#     conn.execute("ALTER TABLE vm_instances ADD COLUMN new_field TEXT")
#


def migrate_v1_to_v2(conn: sqlite3.Connection) -> None:
    """Add runner_pid column for per-VM process architecture."""
    # Check if column already exists
    cursor = conn.execute("PRAGMA table_info(vm_instances)")
    columns = [row[1] for row in cursor.fetchall()]

    if "runner_pid" not in columns:
        conn.execute("ALTER TABLE vm_instances ADD COLUMN runner_pid INTEGER")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_vm_runner_pid ON vm_instances(runner_pid)")


MIGRATIONS: Dict[int, callable] = {
    2: migrate_v1_to_v2,
    # Future migrations will be added here
    # 3: migrate_v2_to_v3,
}


@dataclass
class VMInstance:
    """Represents a VM instance in the state database."""

    id: str
    name: str
    config_path: Optional[str]
    config_data: Dict[str, Any]
    status: str  # 'created', 'running', 'stopped', 'failed'
    pid: Optional[int]  # QEMU process PID
    runner_pid: Optional[int] = None  # VM runner process PID (per-VM architecture)
    socket_path: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class XDGDirectories:
    """
    XDG Base Directory Specification compliance for MAQET directories.

    Provides proper directory structure following Linux standards.
    """

    def __init__(self, custom_data_dir: Optional[Path] = None) -> None:
        """
        Initialize XDG directories.

        Args:
            custom_data_dir: Override default data directory (for testing)
        """
        self._custom_data_dir = custom_data_dir
        self._ensure_directories()

    @property
    def data_dir(self) -> Path:
        """Get XDG data directory (~/.local/share/maqet/)."""
        if self._custom_data_dir:
            return self._custom_data_dir
        base = os.getenv("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
        return Path(base) / "maqet"

    @property
    def runtime_dir(self) -> Path:
        """Get XDG runtime directory (/run/user/1000/maqet/)."""
        if self._custom_data_dir:
            # Use custom runtime dir adjacent to custom data dir
            return self._custom_data_dir.parent / "runtime"
        base = os.getenv("XDG_RUNTIME_DIR", f"/tmp/maqet-{os.getuid()}")
        return Path(base) / "maqet"

    @property
    def config_dir(self) -> Path:
        """Get XDG config directory (~/.config/maqet/)."""
        if self._custom_data_dir:
            # Use custom config dir adjacent to custom data dir
            return self._custom_data_dir.parent / "config"
        base = os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
        return Path(base) / "maqet"

    @property
    def database_path(self) -> Path:
        """Get database file path."""
        return self.data_dir / "instances.db"

    @property
    def vm_definitions_dir(self) -> Path:
        """Get VM definitions directory."""
        return self.data_dir / "vm-definitions"

    @property
    def sockets_dir(self) -> Path:
        """Get QMP sockets directory."""
        return self.runtime_dir / "sockets"

    @property
    def pids_dir(self) -> Path:
        """Get PID files directory."""
        return self.runtime_dir / "pids"

    @property
    def locks_dir(self) -> Path:
        """Get lock files directory for VM start operations."""
        return self.runtime_dir / "locks"

    @property
    def templates_dir(self) -> Path:
        """Get VM templates directory."""
        return self.config_dir / "templates"

    def _ensure_directories(self) -> None:
        """Create XDG-compliant directory structure."""
        dirs = [
            self.data_dir,
            self.vm_definitions_dir,
            self.runtime_dir,
            self.sockets_dir,
            self.pids_dir,
            self.locks_dir,
            self.config_dir,
            self.templates_dir,
        ]

        for directory in dirs:
            directory.mkdir(parents=True, exist_ok=True)


class StateManager:
    """
    Manages VM instance state with SQLite backend.

    Provides persistent storage for VM definitions, process tracking,
    and session management following XDG directory standards.

    # NOTE: Good - XDG compliance ensures proper file locations across
    # different
    # Linux distributions and user configurations. Respects user preferences.
    # NOTE: Cleanup of stale socket/PID files IS implemented in
    # cleanup_dead_processes(),
    #       which runs on startup and cleans orphaned processes.

    # ARCHITECTURAL DECISION: Database Migration Strategy
    # ================================================
    # Current: No migration system - schema changes require manual database
    # deletion
    # Impact: Users must delete ~/.local/share/maqet/instances.db after
    # upgrades that change schema
    #
    # Future Migration Strategy (when needed):
    #   1. Version table to track schema version (e.g., schema_version INTEGER)
    #   2. Migration scripts for each schema change:
    #      - Option A: Embedded Python migrations (simple, no dependencies)
    #      - Option B: alembic/yoyo-migrations (robust, industry-standard)
    # 3. Automatic backup before migration
    # (~/.local/share/maqet/backups/instances.db.YYYYMMDD)
    #   4. Rollback capability for failed migrations
    #   5. Migration status logging (success/failure/skipped)
    #
    # Decision: Deferred until schema stabilizes (currently in rapid
    # development)
    # Workaround: Document breaking changes in release notes, instruct users to
    # delete DB
    # Timeline: Implement before 1.0 release when API/schema stabilizes
    """

    def __init__(self, custom_data_dir: Optional[str] = None):
        """
        Initialize state manager.

        Args:
            custom_data_dir: Override default data directory
        """
        # Pass custom_data_dir to XDGDirectories instead of modifying environment
        custom_path = Path(custom_data_dir) if custom_data_dir else None
        self.xdg = XDGDirectories(custom_data_dir=custom_path)
        self._init_database()

        # Run database migrations if needed
        self.run_migrations()

        # Automatically clean up dead processes and stale files on startup
        cleaned = self.cleanup_dead_processes()
        if cleaned:
            LOG.debug(f"Startup cleanup completed: {len(cleaned)} VMs cleaned")

    def _init_database(self) -> None:
        """Initialize SQLite database with required tables."""
        with self._get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS vm_instances (
                    id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    config_path TEXT,
                    config_data TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'created',
                    pid INTEGER,
                    socket_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_vm_name ON vm_instances(name);
                CREATE INDEX IF NOT EXISTS idx_vm_status ON vm_instances(status);
                CREATE INDEX IF NOT EXISTS idx_vm_pid ON vm_instances(pid);

                CREATE TRIGGER IF NOT EXISTS update_timestamp
                    AFTER UPDATE ON vm_instances
                BEGIN
                    UPDATE vm_instances SET updated_at = CURRENT_TIMESTAMP
                    WHERE id = NEW.id;
                END;

                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT
                );
            """
            )

            # Initialize schema version if this is a new database
            current_version = self.get_schema_version()
            if current_version == 0:
                self._set_schema_version(1, "Initial schema")

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get database connection with proper error handling.

        Uses WAL (Write-Ahead Logging) mode to reduce lock contention and
        implements retry logic for transient "database is locked" errors.

        # TODO(architect, 2025-10-10): [PERF] SQLite connection management has race conditions
        # Context: Retry logic helps but doesn't eliminate all races. No connection pooling,
        # opens new connection per operation. Issue #6 in ARCHITECTURAL_REVIEW.md.
        #
        # Recommendation: Implement connection pooling with Queue(maxsize=10) and threading.Lock
        # Alternative: Switch to PostgreSQL for production use
        #
        # Effort: Medium (3-4 days)
        # Priority: High (should fix for 1.0)
        # See: ARCHITECTURAL_REVIEW.md Issue #6

        Yields:
            sqlite3.Connection: Database connection

        Raises:
            DatabaseError: If connection fails after retries
            DatabaseLockError: If database remains locked after all retries
        """
        max_retries = Retries.DB_OPERATION
        retry_delay = Intervals.DB_RETRY_BASE

        conn = None
        for attempt in range(max_retries):
            try:
                conn = sqlite3.connect(
                    str(self.xdg.database_path),
                    timeout=Timeouts.DB_LOCK,
                )
                conn.row_factory = sqlite3.Row

                # Enable WAL mode and pragmas for better concurrent access
                # WAL allows readers and writers to work simultaneously
                conn.execute(f"PRAGMA journal_mode={DBConstants.JOURNAL_MODE}")
                conn.execute(f"PRAGMA synchronous={DBConstants.SYNCHRONOUS}")
                conn.execute(f"PRAGMA foreign_keys={DBConstants.FOREIGN_KEYS}")

                break  # Connection successful

            except sqlite3.OperationalError as e:
                if (
                    "database is locked" in str(e).lower()
                    and attempt < max_retries - 1
                ):
                    # Retry with exponential backoff
                    wait_time = retry_delay * (2**attempt)
                    from maqet.logger import LOG

                    LOG.debug(
                        f"Database locked (attempt {
                            attempt + 1}/{max_retries}), "
                        f"retrying in {wait_time:.2f}s"
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    # Final attempt failed or non-lock error
                    if "database is locked" in str(e).lower():
                        raise DatabaseLockError(
                            f"Database locked after {max_retries} attempts "
                            f"({Timeouts.DB_LOCK}s timeout per attempt). "
                            f"Another process may be holding a lock."
                        )
                    else:
                        raise DatabaseError(
                            f"Failed to connect to database: {e}"
                        )

        if conn is None:
            raise DatabaseError("Failed to establish database connection")

        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def create_vm(
        self,
        name: str,
        config_data: Dict[str, Any],
        config_path: Optional[str] = None,
    ) -> str:
        """
        Create a new VM instance.

        Args:
            name: VM name (must be unique)
            config_data: VM configuration dictionary
            config_path: Optional path to config file

        Returns:
            VM instance ID

        Raises:
            StateManagerError: If validation fails or DB operation fails
        """
        # Validation: Check VM name
        if not name or not name.strip():
            raise StateManagerError("VM name cannot be empty")

        # Check name length (prevent filesystem issues with very long names)
        if len(name) > 255:
            raise StateManagerError(
                f"VM name too long ({len(
                    name)} chars). Maximum is 255 characters."
            )

        # Validate name contains only safe characters (alphanumeric, dash,
        # underscore, dot)
        if not re.match(r"^[a-zA-Z0-9._-]+$", name):
            raise StateManagerError(
                f"VM name '{name}' contains invalid characters. "
                f"Only alphanumeric, dash (-), underscore (_), and dot (.) are allowed."
            )

        # Check for name conflicts BEFORE attempting insert
        # Provides clearer error message than SQLite IntegrityError
        existing_vm = self.get_vm(name)
        if existing_vm:
            raise StateManagerError(
                f"VM with name '{name}' already exists (ID: {existing_vm.id}). "
                f"Use 'maqet rm {name}' to remove it first, "
                f"or choose a different name."
            )

        # Validation: Check config_data size to prevent DB bloat
        config_json = benedict(config_data).to_json()
        config_size = len(config_json.encode("utf-8"))
        max_config_size = 10 * 1024 * 1024  # 10MB limit

        if config_size > max_config_size:
            raise StateManagerError(
                f"Configuration data too large ({config_size} bytes, max {
                    max_config_size}). "
                f"Consider reducing storage device configurations or using external config files."
            )

        vm_id = str(uuid.uuid4())

        try:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO vm_instances (id, name, config_path, config_data, status)
                    VALUES (?, ?, ?, ?, 'created')
                """,
                    (vm_id, name, config_path, config_json),
                )
        except sqlite3.IntegrityError as e:
            raise StateManagerError(f"VM with name '{name}' already exists")
        except sqlite3.OperationalError as e:
            # Handle disk full, database locked, etc.
            error_msg = str(e).lower()
            if "disk" in error_msg or "space" in error_msg:
                raise StateManagerError(
                    f"Cannot create VM: Disk full or insufficient space. "
                    f"Free up disk space and try again. Error: {e}"
                )
            elif "locked" in error_msg:
                raise StateManagerError(
                    f"Cannot create VM: Database is locked. "
                    f"Another process may be accessing it. Retry in a moment. Error: {
                        e}"
                )
            else:
                raise StateManagerError(
                    f"Database error while creating VM: {e}"
                )
        except Exception as e:
            # Log unexpected errors with context
            from ..logger import LOG

            LOG.error(
                f"Unexpected error creating VM '{name}' (ID: {vm_id}): {
                    type(e).__name__}: {e}"
            )
            raise StateManagerError(f"Failed to create VM: {e}")

        return vm_id

    def get_vm(self, identifier: str) -> Optional[VMInstance]:
        """
        Get VM instance by ID or name.

        Optimized to use indexes by trying ID lookup first (PRIMARY KEY),
        then name lookup (idx_vm_name index) if not found.

        Args:
            identifier: VM ID or name

        Returns:
            VM instance or None if not found
        """
        # NOTE: SECURITY - Uses parameterized queries, safe from SQL injection
        with self._get_connection() as conn:
            # Try ID first (PRIMARY KEY index - O(log n))
            row = conn.execute(
                "SELECT * FROM vm_instances WHERE id = ?",
                (identifier,),
            ).fetchone()

            if row:
                return self._row_to_vm_instance(row)

            # Try name (idx_vm_name index - O(log n))
            row = conn.execute(
                "SELECT * FROM vm_instances WHERE name = ?",
                (identifier,),
            ).fetchone()

            if row:
                return self._row_to_vm_instance(row)

        return None

    def list_vms(
        self, status_filter: Optional[str] = None
    ) -> List[VMInstance]:
        """
        List all VM instances.

        Args:
            status_filter: Optional status to filter by

        Returns:
            List of VM instances
        """
        with self._get_connection() as conn:
            if status_filter:
                rows = conn.execute(
                    "SELECT * FROM vm_instances WHERE status = ? ORDER BY created_at",
                    (status_filter,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM vm_instances ORDER BY created_at"
                ).fetchall()

            return [self._row_to_vm_instance(row) for row in rows]

    def _validate_pid_ownership(self, pid: int) -> None:
        """
        Validate that PID belongs to current user and is a QEMU process.

        Args:
            pid: Process ID to validate

        Raises:
            ValueError: If PID is invalid, not owned by user, or not a QEMU process
        """
        # psutil is optional - skip PID validation if not available
        if not PSUTIL_AVAILABLE:
            LOG.debug(
                "psutil not available, skipping PID ownership validation. "
                "Install psutil for enhanced security checks."
            )
            return

        try:
            process = psutil.Process(pid)

            # Check if process is owned by current user (Unix only)
            if hasattr(os, "getuid"):
                current_uid = os.getuid()
                process_uid = process.uids().real

                if process_uid != current_uid:
                    raise ValueError(
                        f"PID {pid} is owned by UID {
                            process_uid}, not current user (UID {current_uid}). "
                        f"Refusing to manage process owned by another user for security reasons."
                    )

            # Verify it's a QEMU process
            cmdline = process.cmdline()
            if not cmdline:
                raise ValueError(
                    f"PID {
                        pid} has no command line. Cannot verify it's a QEMU process."
                )

            # Check if command contains 'qemu' (case insensitive)
            is_qemu = any("qemu" in arg.lower() for arg in cmdline)
            if not is_qemu:
                LOG.warning(
                    f"PID {pid} does not appear to be a QEMU process. "
                    f"Command: {' '.join(cmdline[:3])}..."
                )
                # We warn but don't block, as the binary might be renamed

        except psutil.NoSuchProcess:
            raise ValueError(f"PID {pid} does not exist")
        except psutil.AccessDenied:
            raise ValueError(
                f"Access denied when checking PID {
                    pid}. Cannot verify ownership."
            )

    def update_vm_status(
        self,
        identifier: str,
        status: str,
        pid: Optional[int] = None,
        runner_pid: Optional[int] = None,
        socket_path: Optional[str] = None,
    ) -> bool:
        """
        Update VM status and process information.

        Optimized to use indexes by trying ID lookup first (PRIMARY KEY),
        then name lookup (idx_vm_name index) if not found.

        Args:
            identifier: VM ID or name
            status: New status
            pid: QEMU process ID (if running)
            runner_pid: VM runner process ID (if running)
            socket_path: QMP socket path (if running)

        Returns:
            True if updated, False if VM not found

        Raises:
            ValueError: If PID ownership validation fails
        """
        # Security: Validate PID ownership if provided
        if pid is not None:
            try:
                self._validate_pid_ownership(pid)
            except ValueError as e:
                from ..logger import LOG

                LOG.error(f"PID validation failed: {e}")
                raise

        if runner_pid is not None:
            try:
                self._validate_pid_ownership(runner_pid)
            except ValueError as e:
                from ..logger import LOG

                LOG.error(f"Runner PID validation failed: {e}")
                raise

        with self._get_connection() as conn:
            # Try ID first (PRIMARY KEY index - O(log n))
            cursor = conn.execute(
                """
                UPDATE vm_instances
                SET status = ?, pid = ?, runner_pid = ?, socket_path = ?
                WHERE id = ?
            """,
                (status, pid, runner_pid, socket_path, identifier),
            )

            if cursor.rowcount > 0:
                return True

            # Try name (idx_vm_name index - O(log n))
            cursor = conn.execute(
                """
                UPDATE vm_instances
                SET status = ?, pid = ?, runner_pid = ?, socket_path = ?
                WHERE name = ?
            """,
                (status, pid, runner_pid, socket_path, identifier),
            )

            return cursor.rowcount > 0

    def remove_vm(self, identifier: str) -> bool:
        """
        Remove VM instance from database.

        Optimized to use indexes by trying ID lookup first (PRIMARY KEY),
        then name lookup (idx_vm_name index) if not found.

        Args:
            identifier: VM ID or name

        Returns:
            True if removed, False if VM not found
        """
        with self._get_connection() as conn:
            # Try ID first (PRIMARY KEY index - O(log n))
            cursor = conn.execute(
                "DELETE FROM vm_instances WHERE id = ?",
                (identifier,),
            )

            if cursor.rowcount > 0:
                return True

            # Try name (idx_vm_name index - O(log n))
            cursor = conn.execute(
                "DELETE FROM vm_instances WHERE name = ?",
                (identifier,),
            )

            return cursor.rowcount > 0

    def cleanup_dead_processes(self) -> List[str]:
        """
        Clean up VMs with dead processes and stale files.

        This method:
        - Checks all VMs marked as 'running' in database
        - Verifies their processes are actually alive
        - Updates status to 'stopped' for dead processes
        - Removes stale socket and PID files

        Returns:
            List of VM IDs that were cleaned up
        """
        cleaned_up = []
        running_vms = self.list_vms(status_filter="running")

        for vm in running_vms:
            if vm.pid and not self._is_process_alive(vm.pid):
                LOG.info(
                    f"Cleaning up dead VM {
                        vm.name} (ID: {vm.id}, PID: {vm.pid})"
                )

                # Update database status
                self.update_vm_status(
                    vm.id, "stopped", pid=None, socket_path=None
                )

                # Clean up stale socket file
                socket_path = self.get_socket_path(vm.id)
                if socket_path.exists():
                    try:
                        socket_path.unlink()
                        LOG.debug(f"Removed stale socket: {socket_path}")
                    except OSError as e:
                        LOG.warning(
                            f"Failed to remove stale socket {socket_path}: {e}"
                        )

                # Clean up stale PID file
                pid_path = self.get_pid_path(vm.id)
                if pid_path.exists():
                    try:
                        pid_path.unlink()
                        LOG.debug(f"Removed stale PID file: {pid_path}")
                    except OSError as e:
                        LOG.warning(
                            f"Failed to remove stale PID file {pid_path}: {e}"
                        )

                cleaned_up.append(vm.id)

        if cleaned_up:
            LOG.info(
                f"Cleaned up {len(cleaned_up)} dead VM(s): {
                    ', '.join(cleaned_up)}"
            )

        return cleaned_up

    def _is_process_alive(self, pid: int) -> bool:
        """Check if process is still running."""
        try:
            os.kill(pid, 0)  # Send signal 0 to check if process exists
            return True
        except (OSError, ProcessLookupError):
            return False

    def _row_to_vm_instance(self, row: sqlite3.Row) -> VMInstance:
        """Convert database row to VMInstance object."""
        config_data = benedict.from_json(row["config_data"])

        # Handle runner_pid which may not exist in older schemas
        runner_pid = row["runner_pid"] if "runner_pid" in row.keys() else None

        return VMInstance(
            id=row["id"],
            name=row["name"],
            config_path=row["config_path"],
            config_data=config_data,
            status=row["status"],
            pid=row["pid"],
            runner_pid=runner_pid,
            socket_path=row["socket_path"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def get_socket_path(self, vm_id: str) -> Path:
        """Get QMP socket path for VM."""
        return self.xdg.sockets_dir / f"{vm_id}.sock"

    def get_pid_path(self, vm_id: str) -> Path:
        """Get PID file path for VM."""
        return self.xdg.pids_dir / f"{vm_id}.pid"

    def get_lock_path(self, vm_id: str) -> Path:
        """Get lock file path for VM start operations."""
        return self.xdg.locks_dir / f"{vm_id}.lock"

    def update_vm_config(
        self, identifier: str, new_config: Dict[str, Any]
    ) -> bool:
        """
        Update VM configuration in database.

        Optimized to use indexes by trying ID lookup first (PRIMARY KEY),
        then name lookup (idx_vm_name index) if not found.

        Args:
            identifier: VM name or ID
            new_config: New configuration data

        Returns:
            True if update successful, False if VM not found

        Raises:
            StateManagerError: If database operation fails
        """
        try:
            with self._get_connection() as conn:
                # Try ID first (PRIMARY KEY index - O(log n))
                cursor = conn.execute(
                    """
                    UPDATE vm_instances
                    SET config_data = ?
                    WHERE id = ?
                """,
                    (json.dumps(new_config), identifier),
                )

                if cursor.rowcount > 0:
                    return True

                # Try name (idx_vm_name index - O(log n))
                cursor = conn.execute(
                    """
                    UPDATE vm_instances
                    SET config_data = ?
                    WHERE name = ?
                """,
                    (json.dumps(new_config), identifier),
                )

                return cursor.rowcount > 0

        except sqlite3.Error as e:
            raise StateManagerError(f"Database error updating VM config: {e}")
        except Exception as e:
            raise StateManagerError(f"Error updating VM config: {e}")

    def get_schema_version(self) -> int:
        """
        Get current database schema version.

        Returns:
            Current schema version, or 0 if schema_version table doesn't exist
        """
        try:
            with self._get_connection() as conn:
                result = conn.execute(
                    "SELECT MAX(version) FROM schema_version"
                ).fetchone()
                return result[0] if result[0] is not None else 0
        except sqlite3.OperationalError:
            # schema_version table doesn't exist (pre-migration database)
            return 0

    def _set_schema_version(self, version: int, description: str = "") -> None:
        """
        Set database schema version.

        Args:
            version: Schema version number
            description: Optional description of the schema version
        """
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO schema_version (version, description, applied_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                """,
                (version, description),
            )

    def backup_database(self) -> Path:
        """
        Create timestamped database backup.

        Returns:
            Path to backup file

        Raises:
            StateManagerError: If backup fails
        """
        try:
            # Create backups directory
            backup_dir = self.xdg.data_dir / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Generate timestamped backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            schema_version = self.get_schema_version()
            backup_filename = f"instances_v{schema_version}_{timestamp}.db"
            backup_path = backup_dir / backup_filename

            # Copy database file
            shutil.copy2(self.xdg.database_path, backup_path)

            LOG.info(f"Database backed up to {backup_path}")
            return backup_path

        except Exception as e:
            raise StateManagerError(f"Failed to backup database: {e}")

    def run_migrations(self) -> None:
        """
        Run all pending database migrations.

        Migrations are applied sequentially from current version to target version.
        Database is automatically backed up before applying migrations.

        Raises:
            StateManagerError: If migration fails
        """
        current_version = self.get_schema_version()
        target_version = max(MIGRATIONS.keys()) if MIGRATIONS else 1

        if current_version >= target_version:
            LOG.debug(
                f"Database schema is up to date (version {current_version})"
            )
            return

        LOG.info(
            f"Migrating database from version {
                current_version} to {target_version}"
        )

        # Backup database before migration
        try:
            backup_path = self.backup_database()
            LOG.info(f"Pre-migration backup created: {backup_path}")
        except Exception as e:
            LOG.error(f"Failed to create backup before migration: {e}")
            raise StateManagerError(
                f"Cannot proceed with migration without backup: {e}"
            )

        # Apply migrations sequentially
        for version in range(current_version + 1, target_version + 1):
            if version in MIGRATIONS:
                try:
                    self._apply_migration(version, MIGRATIONS[version])
                except Exception as e:
                    error_msg = (
                        f"Migration to version {version} failed: {e}\n"
                        f"Database backup is available at: {backup_path}\n"
                        f"To rollback, restore the backup:\n"
                        f"  cp {backup_path} {self.xdg.database_path}"
                    )
                    LOG.error(error_msg)
                    raise StateManagerError(error_msg)

        LOG.info(
            f"Database migration completed successfully to version {
                target_version}"
        )

    def _apply_migration(self, version: int, migration_func: callable) -> None:
        """
        Apply a single database migration.

        Args:
            version: Target schema version
            migration_func: Migration function to execute

        Raises:
            StateManagerError: If migration fails
        """
        LOG.info(f"Applying migration to version {version}")

        try:
            with self._get_connection() as conn:
                # Start transaction
                conn.execute("BEGIN IMMEDIATE")

                try:
                    # Execute migration function
                    migration_func(conn)

                    # Update schema version
                    conn.execute(
                        """
                        INSERT INTO schema_version (version, description, applied_at)
                        VALUES (?, ?, CURRENT_TIMESTAMP)
                        """,
                        (version, f"Migration to version {version}"),
                    )

                    # Commit transaction
                    conn.commit()
                    LOG.info(
                        f"Migration to version {
                            version} completed successfully"
                    )

                except Exception as e:
                    # Rollback on error
                    conn.rollback()
                    raise StateManagerError(
                        f"Migration to version {version} failed: {e}"
                    )

        except Exception as e:
            raise StateManagerError(f"Failed to apply migration: {e}")
