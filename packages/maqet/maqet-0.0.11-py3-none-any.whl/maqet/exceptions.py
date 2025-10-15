"""
Maqet Exception Hierarchy

Provides specific exception types for better error handling and debugging.
All exceptions inherit from MaqetError base class for easy catching.

Exception Categories:
- Configuration errors: Config file issues, validation failures
- VM lifecycle errors: VM creation, start, stop, not found
- QMP errors: QMP connection and command failures
- Storage errors: Storage device creation and management
- Snapshot errors: Snapshot operations (create, load, list)
- State management errors: Database and state tracking
- Process errors: VM runner process management
- IPC errors: Inter-process communication failures
"""


class MaqetError(Exception):
    """Base exception for all Maqet errors."""


# Configuration Errors
class ConfigurationError(MaqetError):
    """Configuration-related errors."""


class ConfigFileNotFoundError(ConfigurationError):
    """Configuration file not found."""


class ConfigValidationError(ConfigurationError):
    """Configuration validation failed."""


class InvalidConfigurationError(ConfigurationError):
    """Configuration is invalid or malformed."""


# VM Lifecycle Errors
class VMLifecycleError(MaqetError):
    """VM lifecycle operation errors."""


class VMNotFoundError(VMLifecycleError):
    """VM not found in database."""


class VMAlreadyExistsError(VMLifecycleError):
    """VM with this name already exists."""


class VMAlreadyRunningError(VMLifecycleError):
    """VM is already running."""


class VMNotRunningError(VMLifecycleError):
    """VM is not running."""


class VMStartError(VMLifecycleError):
    """Failed to start VM."""


class VMStopError(VMLifecycleError):
    """Failed to stop VM."""


# QMP Errors
class QMPError(MaqetError):
    """QMP command errors."""


class QMPConnectionError(QMPError):
    """Failed to connect to QMP socket."""


class QMPCommandError(QMPError):
    """QMP command execution failed."""


class QMPTimeoutError(QMPError):
    """QMP command timed out."""


# Storage Errors
class StorageError(MaqetError):
    """Storage operation errors."""


class StorageDeviceNotFoundError(StorageError):
    """Storage device not found."""


class StorageCreationError(StorageError):
    """Failed to create storage device."""


class StorageValidationError(StorageError):
    """Storage configuration validation failed."""


# Snapshot Errors
class SnapshotError(MaqetError):
    """Snapshot operation errors."""


class SnapshotNotFoundError(SnapshotError):
    """Snapshot not found."""


class SnapshotCreationError(SnapshotError):
    """Failed to create snapshot."""


class SnapshotLoadError(SnapshotError):
    """Failed to load snapshot."""


class SnapshotDeleteError(SnapshotError):
    """Failed to delete snapshot."""


# State Management Errors
class StateError(MaqetError):
    """State management errors."""


class DatabaseError(StateError):
    """Database operation failed."""


class DatabaseLockError(DatabaseError):
    """Database is locked (timeout waiting for lock)."""


# Process Management Errors
class ProcessError(MaqetError):
    """Process management errors."""


class RunnerProcessError(ProcessError):
    """VM runner process error."""


class RunnerSpawnError(ProcessError):
    """Failed to spawn VM runner."""


class ProcessNotFoundError(ProcessError):
    """Process not found or already dead."""


# IPC Errors
class IPCError(MaqetError):
    """Inter-process communication errors."""


class IPCConnectionError(IPCError):
    """Failed to connect to IPC socket."""


class IPCTimeoutError(IPCError):
    """IPC communication timed out."""


class IPCCommandError(IPCError):
    """IPC command execution failed."""


# Legacy Exception Aliases (for backward compatibility)
# These map old exception names to new hierarchy

# Old: StateManagerError -> New: StateError
class StateManagerError(StateError):
    """DEPRECATED: Use StateError instead."""


# Old: VMManagerError -> New: VMLifecycleError
class VMManagerError(VMLifecycleError):
    """DEPRECATED: Use VMLifecycleError or specific subclass instead."""


# Old: QMPManagerError -> New: QMPError
class QMPManagerError(QMPError):
    """DEPRECATED: Use QMPError or specific subclass instead."""


# Old: SnapshotCoordinatorError -> New: SnapshotError
class SnapshotCoordinatorError(SnapshotError):
    """DEPRECATED: Use SnapshotError or specific subclass instead."""


# Old: ProcessSpawnerError -> New: RunnerSpawnError
class ProcessSpawnerError(RunnerSpawnError):
    """DEPRECATED: Use RunnerSpawnError instead."""


# Old: VMRunnerError -> New: RunnerProcessError
class VMRunnerError(RunnerProcessError):
    """DEPRECATED: Use RunnerProcessError instead."""


# Old: MachineError -> New: VMLifecycleError
class MachineError(VMLifecycleError):
    """DEPRECATED: Use VMLifecycleError or specific subclass instead."""


# Old: UnixSocketIPCServerError -> New: IPCError
class UnixSocketIPCServerError(IPCError):
    """DEPRECATED: Use IPCError or specific subclass instead."""


# Old: RunnerClientError -> New: IPCError
class RunnerClientError(IPCError):
    """DEPRECATED: Use IPCError or specific subclass instead."""


# Old: KeyboardEmulatorError -> New: QMPError
class KeyboardEmulatorError(QMPError):
    """DEPRECATED: Use QMPError instead."""


# Old: ConfigError -> New: ConfigurationError
class ConfigError(ConfigurationError):
    """DEPRECATED: Use ConfigurationError instead."""
