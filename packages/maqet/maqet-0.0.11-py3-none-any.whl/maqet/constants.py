"""
Maqet Constants and Defaults

Centralizes magic numbers for maintainability and documentation.
All timeout values are in seconds unless otherwise noted.
"""


class Timeouts:
    """Timeout values in seconds."""

    # VM operations
    VM_START = 30
    VM_STOP = 30
    VM_GRACEFUL_SHUTDOWN = 5
    VM_GRACEFUL_SHUTDOWN_SHORT = 2  # Shorter timeout for cleanup/exit scenarios
    VM_FORCE_KILL = 5

    # IPC operations
    IPC_CONNECT = 10
    IPC_COMMAND = 10
    IPC_SOCKET_WAIT = 5
    IPC_HEALTH_CHECK = 1

    # Process operations
    PROCESS_SPAWN = 30
    PROCESS_KILL = 5
    PROCESS_WAIT_AFTER_KILL = 1

    # QEMU operations
    QEMU_START = 60
    QEMU_HEALTH_CHECK = 5
    QEMU_QMP_THREAD_JOIN = 2
    QMP_COMMAND = 30  # QMP command execution timeout

    # Database operations
    DB_LOCK = 30  # SQLite busy_timeout
    DB_OPERATION_RETRY = 5  # Per-attempt timeout for DB operations

    # Cleanup operations
    CLEANUP_VM_STOP = 5
    CLEANUP_RUNNER_STOP = 5

    # Binary validation
    BINARY_VERSION_CHECK = 5


class Intervals:
    """Polling and check intervals in seconds."""

    # Event loop and polling
    EVENT_LOOP_SLEEP = 0.05  # 50ms
    SOCKET_POLL = 0.1  # 100ms
    PROCESS_POLL = 0.5  # 500ms
    SHUTDOWN_POLL = 0.5  # Polling interval during VM shutdown

    # Retry intervals
    DB_RETRY_BASE = 0.1  # Base interval for exponential backoff (100ms)
    IPC_BACKOFF_BASE = 0.5  # Base interval for IPC retry exponential backoff (500ms)
    PROCESS_STARTUP_WAIT = 0.5  # Wait after spawning process

    # Health checks
    VM_HEALTH_CHECK = 0.1  # Check if VM process is alive
    RUNNER_HEALTH_CHECK = 1  # Check if runner process is alive

    # Signal handling
    SIGTERM_WAIT = 2.0  # Wait after SIGTERM before sending SIGKILL
    CLEANUP_WAIT = 1.0  # Wait for DB status updates and cleanup operations


class Retries:
    """Retry counts for operations."""

    # Database operations
    DB_OPERATION = 3  # Max attempts for DB operations with locks
    DB_LOCK_MAX_ATTEMPTS = 10  # Max attempts for lock acquisition

    # IPC operations
    IPC_CONNECT = 3  # Max attempts for IPC connection
    IPC_MAX_RETRIES = 3  # Max attempts for IPC operations (alias for consistency)
    SOCKET_CONNECT = 5

    # Snapshot operations
    SNAPSHOT_OPERATION = 3  # Max attempts for transient snapshot failures


class Limits:
    """Size and count limits."""

    # Configuration
    CONFIG_MAX_SIZE = 1024 * 1024  # 1MB
    CONFIG_MAX_DEPTH = 10  # Max depth for nested configuration

    # Logging
    LOG_FILE_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_MAX_BACKUPS = 5

    # Resource limits
    MAX_CONCURRENT_VMS = 100
    MAX_STORAGE_DEVICES = 16  # QEMU limit
    MAX_SNAPSHOT_NAME_LENGTH = 255

    # IPC
    MAX_IPC_MESSAGE_SIZE = 1024 * 1024  # 1MB
    MAX_CONCURRENT_WORKERS = 10  # For parallel VM cleanup


class Paths:
    """Default path patterns.

    These use format strings that can be filled in at runtime.
    """

    # Runtime paths (XDG_RUNTIME_DIR)
    SOCKET_PATTERN = "{runtime_dir}/maqet/sockets/{vm_id}.sock"
    PID_PATTERN = "{runtime_dir}/maqet/pids/{vm_id}.pid"

    # Data paths (XDG_DATA_HOME)
    DATABASE_PATTERN = "{data_dir}/instances.db"
    VM_DEFINITIONS_PATTERN = "{data_dir}/vm-definitions"
    LOG_PATTERN = "{data_dir}/logs/vm_{vm_id}.log"
    RUNNER_LOG_PATTERN = "{data_dir}/logs/runner_{vm_id}.log"

    # Config paths (XDG_CONFIG_HOME)
    CONFIG_PATTERN = "{config_dir}/maqet/config.toml"


class Database:
    """Database-specific constants."""

    # Schema version
    SCHEMA_VERSION = 2

    # SQLite pragmas
    JOURNAL_MODE = "WAL"  # Write-Ahead Logging for better concurrency
    SYNCHRONOUS = "NORMAL"  # Balance between safety and performance
    FOREIGN_KEYS = "ON"  # Enable foreign key constraints

    # Table names
    TABLE_VM_INSTANCES = "vm_instances"
    TABLE_SCHEMA_VERSION = "schema_version"


class QMP:
    """QMP (QEMU Machine Protocol) constants."""

    # Key hold time (milliseconds)
    DEFAULT_KEY_HOLD_TIME = 100

    # QMP connection
    CONNECTION_TIMEOUT = 10
    COMMAND_TIMEOUT = 30

    # Screenshot formats
    SCREENSHOT_FORMAT_PPM = "ppm"
    SCREENSHOT_FORMAT_PNG = "png"


class ProcessManagement:
    """Process management constants."""

    # Process states
    STATE_RUNNING = "running"
    STATE_STOPPED = "stopped"
    STATE_CREATED = "created"
    STATE_FAILED = "failed"

    # Signal handling
    SIGNAL_GRACEFUL = 15  # SIGTERM
    SIGNAL_FORCE = 9  # SIGKILL


class Defaults:
    """Default values for various operations."""

    # VM configuration defaults
    VM_MEMORY = "2G"
    VM_CPU_CORES = 2
    VM_DISPLAY = "none"  # Headless by default
    VM_VGA = "none"  # No VGA for headless

    # Storage defaults
    STORAGE_INTERFACE = "virtio"
    STORAGE_FORMAT = "qcow2"

    # Snapshot defaults
    SNAPSHOT_TIMEOUT = 60  # seconds

    # Binary detection
    QEMU_BINARY_PATHS = [
        "/usr/bin/qemu-system-x86_64",
        "/usr/local/bin/qemu-system-x86_64",
        "/opt/homebrew/bin/qemu-system-x86_64",  # macOS Homebrew
    ]

    QEMU_IMG_BINARY_PATHS = [
        "/usr/bin/qemu-img",
        "/usr/local/bin/qemu-img",
        "/opt/homebrew/bin/qemu-img",  # macOS Homebrew
    ]
