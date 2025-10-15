# Architectural Review Report

**Date**: 2025-10-10
**Reviewer**: AGENT-ARCHITECT
**Codebase**: maqet v1.0 (Python-based QEMU VM automation framework)

## Executive Summary

**Total Issues Found**: 23

- **Critical Issues**: 2 (must fix before 1.0 release)
- **High Priority**: 7 (architectural flaws, technical debt)
- **Medium Priority**: 9 (code quality, maintainability)
- **Low Priority**: 5 (minor improvements, nice-to-haves)

**Overall Assessment**: The maqet codebase demonstrates **solid architectural design** with excellent use of decorators, plugin systems, and separation of concerns. The unified API system (@api_method) is innovative and well-implemented. However, several critical architectural issues need addressing before 1.0 release, particularly around cross-process communication (QMP), the god object pattern in the Maqet class, and inconsistent error handling.

**Code Metrics**:

- Production code: ~5,639 lines (maqet/*.py)
- Test code: ~13,580 lines (tests/)
- Test-to-code ratio: 2.4:1 (excellent coverage effort)
- Total Python files: 94

---

## Critical Issues (Fix Immediately)

### Issue #1: Cross-Process QMP Communication Impossible

**Location**: `maqet/machine.py:129-158`
**Category**: ARCH
**Problem**: QEMUMachine instances cannot be shared between processes because Python cannot pickle file descriptors (QMP sockets). When CLI exits, QMP connections are destroyed, making commands like `maqet qmp myvm query-status` fail in subsequent invocations.

**Impact**:

- **Major feature limitation**: QMP commands don't work in CLI mode (only Python API mode)
- Confusing UX: Users expect `maqet qmp` to work but get "No such file or directory" errors
- Documented workaround exists (use Python API), but CLI is the primary interface

**Root Cause**: Machine instances stored in memory (`_machines` dict) are lost when CLI process exits.

**Current Solution**: Long architectural comment explains the limitation and suggests daemon mode (was implemented but removed).

**Recommendation**: Implement one of three solutions:

1. **Direct Socket Communication** (Recommended for 1.0)
   - Bypass QEMUMachine, talk directly to QMP socket
   - Store socket path in database, connect on demand
   - Effort: Medium (2-4 days)
   - Pros: No daemon needed, simpler architecture
   - Cons: Duplicate some QMP protocol handling

2. **Daemon Mode** (Better for 2.0+)
   - Persistent background process managing VMs
   - CLI communicates via DBus/gRPC
   - Effort: Large (1-2 weeks)
   - Pros: Professional architecture, supports advanced features
   - Cons: Complex, adds systemd dependency

3. **Hybrid Approach**
   - Direct socket for simple commands (query-status, screendump)
   - Daemon for complex workflows (keyboard automation, monitoring)
   - Effort: Large (2-3 weeks)

**Decision**: Direct socket communication for 1.0, daemon mode for 2.0.

**Effort**: Medium (2-4 days for direct socket)

---

### Issue #2: God Object Pattern in Maqet Class

**Location**: `maqet/maqet.py:35-1496`
**Category**: ARCH
**Problem**: The `Maqet` class violates Single Responsibility Principle. It handles:

- VM lifecycle management (add, start, stop, rm)
- QMP command execution (qmp, keys, type, screendump)
- Storage/snapshot management (snapshot operations)
- State management coordination
- CLI/API generation coordination
- Configuration parsing and validation
- All in 1,496 lines (largest file in codebase)

**Impact**:

- **Maintainability**: Hard to understand full class scope
- **Testing**: Unit tests difficult (many mocked dependencies)
- **Extensibility**: Adding features requires modifying god object
- **Code reuse**: Logic tightly coupled, hard to extract

**Recommendation**: Refactor into cohesive sub-managers:

```python
class Maqet(AutoRegisterAPI):
    """Unified VM management facade."""

    def __init__(self, data_dir=None):
        self.state_manager = StateManager(data_dir)
        self.vm_manager = VMManager(self.state_manager)  # NEW: start, stop, lifecycle
        self.qmp_manager = QMPManager(self.state_manager)  # NEW: all QMP operations
        self.snapshot_manager = SnapshotCoordinator(self.state_manager)  # NEW: snapshots
        self.config_parser = ConfigParser(self)

    @api_method(cli_name="start", ...)
    def start(self, vm_id: str) -> VMInstance:
        """Delegate to VMManager."""
        return self.vm_manager.start(vm_id)

    @api_method(cli_name="qmp", ...)
    def qmp(self, vm_id: str, command: str, **kwargs):
        """Delegate to QMPManager."""
        return self.qmp_manager.execute(vm_id, command, **kwargs)
```

**Benefits**:

- Each manager has single responsibility
- Easier to test (mock one manager, not entire Maqet)
- Better code organization (VM logic in VMManager, QMP in QMPManager)
- Maintainable file sizes (<500 lines per manager)

**Effort**: Large (1-2 weeks, but can be done incrementally)

---

## High Priority Issues

### Issue #3: Inconsistent Error Handling Strategy

**Location**: Multiple files
**Category**: MAINTAIN
**Problem**: Error handling is inconsistent across the codebase:

- Some methods wrap exceptions and re-raise as MaqetError/MachineError/SnapshotError
- Others let exceptions propagate
- Some use bare `except Exception` (too broad)
- Error messages vary in quality (some helpful, some cryptic)

**Examples**:

```python
# GOOD: Specific error with context (maqet.py:328-351)
except FileNotFoundError as e:
    raise MaqetError(f"Configuration file not found: {e.filename}. Check that the file path is correct.")

# BAD: Bare except with generic message (multiple locations)
except Exception as e:
    raise MaqetError(f"Failed to create VM: {e}")
```

**Recommendation**: Establish error handling guidelines:

1. Create exception hierarchy:

   ```python
   MaqetError (base)
   ├── ConfigurationError
   ├── VMLifecycleError
   ├── QMPError
   ├── StorageError (already exists)
   └── SnapshotError (already exists)
   ```

2. Document when to use each exception type
3. Always provide actionable error messages with:
   - What went wrong
   - Why it happened (if known)
   - How to fix it
4. Never use bare `except Exception` (use specific exceptions)

**Effort**: Medium (3-5 days to standardize)

---

### Issue #4: Machine Class Has Too Many Responsibilities

**Location**: `maqet/machine.py:121-907`
**Category**: ARCH
**Problem**: Machine class handles:

- QEMU process lifecycle
- Configuration validation
- QMP communication
- Storage device setup
- Config handler registry management
- Process cleanup and signal handling

**Impact**: 907-line file, hard to test, tight coupling.

**Recommendation**: Extract responsibilities:

```python
class Machine:
    """VM process lifecycle only."""
    def __init__(self, config_data, vm_id, state_manager):
        self.config_validator = ConfigValidator()  # NEW
        self.qmp_client = QMPClient(vm_id)  # NEW
        self.storage_coordinator = StorageCoordinator(vm_id, config_data)  # NEW

class QMPClient:
    """QMP communication only."""
    def execute(self, command, **kwargs): ...
    def connect(self, socket_path): ...

class ConfigValidator:
    """Configuration validation only."""
    def validate(self, config_data): ...
```

**Effort**: Large (1 week)

---

### Issue #5: Global Mutable State in Module-Level Registry

**Location**: `maqet/config_handlers.py:48-49`, `maqet/api/decorators.py:11`
**Category**: ARCH
**Problem**: Global registries are module-level singletons:

```python
# config_handlers.py
_config_registry = ConfigHandlerRegistry()  # GLOBAL

# api/registry.py
API_REGISTRY = APIRegistry()  # GLOBAL
```

**Impact**:

- Tests interfere with each other (shared global state)
- Cannot have multiple Maqet instances with different configs
- Parallel test execution unreliable
- Hard to reset state between tests

**Recommendation**: Make registries instance-based:

```python
class Maqet:
    def __init__(self):
        self.api_registry = APIRegistry()  # INSTANCE
        self.config_registry = ConfigHandlerRegistry()  # INSTANCE
```

Or use context managers for thread-local registries:

```python
with maqet_context() as maqet:
    # Fresh registry for this context
    maqet.add_vm(...)
```

**Effort**: Medium (4-6 days, requires refactoring decorators)

---

### Issue #6: SQLite Connection Management Has Race Conditions

**Location**: `maqet/state.py:260-324`
**Category**: PERF
**Problem**: Context manager uses retry logic with exponential backoff for "database is locked" errors, but:

- Max 5 retries may not be enough under high load
- No distributed lock coordination (multiple processes can collide)
- WAL mode helps but doesn't eliminate all races
- No connection pooling (opens new connection per operation)

**Current Mitigation**: WAL mode + retry logic (implemented in `_get_connection`)

**Recommendation**: Implement connection pooling:

```python
from contextlib import contextmanager
import threading

class StateManager:
    def __init__(self):
        self._connection_pool = Queue(maxsize=10)
        self._lock = threading.Lock()

    @contextmanager
    def _get_connection(self):
        conn = self._connection_pool.get(timeout=30)
        try:
            yield conn
            conn.commit()
        except:
            conn.rollback()
            raise
        finally:
            self._connection_pool.put(conn)
```

**Alternative**: Switch to client-server database (PostgreSQL) for production use.

**Effort**: Medium (3-4 days)

---

### Issue #7: Snapshot Operations Are Synchronous and Block

**Location**: `maqet/snapshot.py:56-108`, `maqet/snapshot.py:232-363`
**Category**: PERF
**Problem**: All snapshot operations (create/load/list) use `subprocess.run()` which blocks until qemu-img completes. For large disks (100GB+), this can take minutes.

**Impact**:

- CLI freezes during snapshot operations
- No progress indication
- Users don't know if operation is stuck or progressing
- Cannot cancel long-running operations

**Recommendation**: Implement async operations:

```python
import asyncio

async def create_async(self, drive_name, snapshot_name):
    """Async snapshot creation with progress reporting."""
    process = await asyncio.create_subprocess_exec(
        "qemu-img", "snapshot", "-c", snapshot_name, drive_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    # Monitor progress (qemu-img -p for progress)
    async for line in process.stdout:
        yield {"progress": parse_progress(line)}

    await process.wait()
```

**Alternative**: Keep synchronous but add:

- Progress callback parameter
- Timeout warnings ("still working..." messages every 30s)
- Estimated time remaining (based on file size)

**Effort**: Medium (3-5 days for async, 1-2 days for progress reporting)

**Note**: Defer until working with large disks (not critical for 1.0)

---

### Issue #8: Missing Import Validation and Type Checking

**Location**: Multiple files
**Category**: MAINTAIN
**Problem**: Some modules have conditional imports that may fail at runtime:

```python
# Optional psutil import (state.py:30-35)
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
```

**Issues**:

- Functions assume psutil is available, then check flag
- No graceful degradation guidance for users
- Type hints reference types that may not exist
- Mypy doesn't catch these issues

**Recommendation**:

1. Document optional dependencies in README
2. Provide clear error messages when missing:

   ```python
   if not PSUTIL_AVAILABLE:
       LOG.warning("psutil not installed. Install for enhanced process monitoring: pip install psutil")
   ```

3. Use TYPE_CHECKING for optional type hints:

   ```python
   if TYPE_CHECKING:
       import psutil  # Only for type checking
   ```

**Effort**: Small (1-2 hours)

---

### Issue #9: ConfigHandler Decorator System Lacks Discovery Mechanism

**Location**: `maqet/config_handlers.py:52-69`, `maqet/config_handlers.py:96-156`
**Category**: MAINTAIN
**Problem**: Config handlers are registered via decorator at module load time, but:

- No way to list all registered handlers programmatically (for debugging)
- No validation that critical handlers exist
- Typos in config keys silently ignored (handler not found = warning only)
- Circular dependency: decorators register handlers before class definition complete

**Recommendation**:

1. Add handler discovery:

   ```python
   def get_registered_handlers() -> Dict[str, Callable]:
       """Get all registered config handlers for debugging."""
       return _config_registry._handlers.copy()
   ```

2. Validate critical handlers exist at startup:

   ```python
   REQUIRED_HANDLERS = {"binary", "storage", "arguments"}

   def validate_handlers():
       missing = REQUIRED_HANDLERS - set(_config_registry.get_registered_keys())
       if missing:
           raise ConfigError(f"Missing required config handlers: {missing}")
   ```

3. Make typos fail fast (optional strict mode):

   ```python
   def process_configuration(self, config_data, strict=False):
       unhandled = self.get_unhandled_keys(config_data)
       if strict and unhandled:
           raise ConfigError(f"Unknown config keys: {unhandled}")
   ```

**Effort**: Small (2-3 hours)

---

## Medium Priority Issues

### Issue #10: Duplicate Code in Global Options Registration

**Location**: `maqet/generators/cli_generator.py:187-241`
**Category**: REFACTOR
**Problem**: Global options added twice (to main parser and parent parser), exact same code duplicated.

**Recommendation**: Extract to method:

```python
def _add_global_options(self, parser):
    """Add global options to any parser."""
    parser.add_argument("-v", "--verbose", ...)
    # ... rest of options

def _add_global_options_to_parent(self):
    self._add_global_options(self.global_parent)

def _add_global_options_to_main(self):
    self._add_global_options(self.parser)
```

**Effort**: Small (<1 hour)

---

### Issue #11: Magic Numbers in Timeout/Retry Logic

**Location**: Multiple files
**Category**: MAINTAIN
**Problem**: Hardcoded timeouts scattered throughout code:

- `state.py:274`: `retry_delay = 0.1` (why 100ms?)
- `state.py:281`: `timeout=30.0` (why 30 seconds?)
- `machine.py:562`: `time.sleep(2)` (why 2 seconds?)
- `snapshot.py:235`: `timeout: int = 300` (why 5 minutes?)

**Recommendation**: Define constants:

```python
# constants.py
class Timeouts:
    DATABASE_LOCK_RETRY_MS = 100
    DATABASE_OPERATION_SECONDS = 30
    VM_GRACEFUL_SHUTDOWN_SECONDS = 30
    SNAPSHOT_OPERATION_SECONDS = 300
    QMP_COMMAND_SECONDS = 30

class Retries:
    DATABASE_LOCK_MAX_ATTEMPTS = 5
    SNAPSHOT_TRANSIENT_FAILURES = 3
```

**Effort**: Small (1-2 hours)

---

### Issue #12: Inconsistent Path Handling (str vs Path)

**Location**: Multiple files
**Category**: MAINTAIN
**Problem**: Some functions use `str` for paths, others use `pathlib.Path`:

```python
# state.py:676-682 - Returns Path
def get_socket_path(self, vm_id: str) -> Path:
    return self.xdg.sockets_dir / f"{vm_id}.sock"

# maqet.py:398 - Converts back to str
socket_path = str(self.state_manager.get_socket_path(vm.id))
```

**Recommendation**: Standardize on `pathlib.Path` for all internal APIs, convert to `str` only at system boundaries (subprocess calls, QEMUMachine).

**Effort**: Medium (2-3 days to refactor)

---

### Issue #13: _format_nested_value Method Too Complex

**Location**: `maqet/config_handlers.py:218-319`
**Category**: REFACTOR
**Problem**: 101-line recursive method with complex nested conditionals. Cyclomatic complexity too high.

**Recommendation**: Break into smaller methods:

```python
def _format_nested_value(value, stack=None):
    if _is_empty_value(value, stack):
        return _format_empty_value(stack)
    if _is_primitive(value):
        return _format_primitive(value, stack)
    if isinstance(value, list):
        return _format_list(value, stack)
    if isinstance(value, dict):
        return _format_dict(value, stack)
```

**Effort**: Small (2-3 hours)

---

### Issue #14: No Centralized Configuration for Defaults

**Location**: `maqet/config_handlers.py:495-523`, `maqet/machine.py:496`
**Category**: MAINTAIN
**Problem**: Default values scattered throughout code:

- Default memory in `apply_default_configuration()`: `"2G"`
- Default CPU in `apply_default_configuration()`: `"1"`
- Default binary in `_pre_start_validation()`: `"/usr/bin/qemu-system-x86_64"`
- Default network in `apply_default_configuration()`: `"user,id=net0"`

**Recommendation**: Centralize defaults:

```python
# defaults.py
class Defaults:
    MEMORY = "2G"
    CPU = 1
    BINARY = "/usr/bin/qemu-system-x86_64"
    NETWORK_MODE = "user"
    DISPLAY = "gtk"  # or None for headless
```

**Effort**: Small (1-2 hours)

---

### Issue #15: Test Fixtures Not Shared Across Test Types

**Location**: `tests/fixtures/`, `tests/unit/conftest.py`, `tests/e2e/conftest.py`
**Category**: TEST
**Problem**: Each test type (unit/integration/e2e) has its own conftest.py with similar fixtures:

- `temp_data_dir` defined multiple times
- Mock patterns duplicated
- Test VM configs duplicated

**Recommendation**: Create shared fixtures in `tests/conftest.py`:

```python
# tests/conftest.py (root level)
@pytest.fixture
def temp_maqet():
    """Maqet instance with isolated temp directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Maqet(data_dir=str(Path(temp_dir) / "data"))

@pytest.fixture
def minimal_vm_config():
    """Minimal valid VM configuration."""
    return {
        "binary": "/usr/bin/qemu-system-x86_64",
        "memory": "1G",
        "cpu": 1,
    }
```

**Effort**: Small (2-3 hours)

---

### Issue #16: Long Methods in Maqet Class

**Location**: `maqet/maqet.py:203-351`, `maqet/maqet.py:568-666`
**Category**: REFACTOR
**Problem**: Several methods exceed 50 lines (bad smell):

- `add()`: 149 lines (203-351)
- `_remove_all_vms()`: 98 lines (568-666)

**Recommendation**: Extract helper methods:

```python
def add(self, config=None, name=None, empty=False, **kwargs):
    """Create VM - main flow only."""
    if empty:
        return self._create_empty_vm(name)

    config_data = self._load_and_merge_config(config, kwargs)
    name = self._determine_vm_name(name, config_data)
    config_data = self._validate_and_clean_config(config_data, name)

    return self.state_manager.create_vm(name, config_data, config_file)

def _create_empty_vm(self, name): ...
def _load_and_merge_config(self, config, kwargs): ...
def _determine_vm_name(self, name, config_data): ...
def _validate_and_clean_config(self, config_data, name): ...
```

**Effort**: Medium (1-2 days)

---

### Issue #17: No Validation for VM Name Conflicts at Creation

**Location**: `maqet/state.py:326-418`
**Category**: MAINTAIN
**Problem**: VM name uniqueness only enforced by SQLite UNIQUE constraint. Error message is database error, not user-friendly:

```python
except sqlite3.IntegrityError as e:
    raise StateManagerError(f"VM with name '{name}' already exists")
```

**Recommendation**: Check before inserting:

```python
def create_vm(self, name, config_data, config_path=None):
    # Validate name doesn't exist first
    if self.get_vm(name):
        raise StateManagerError(
            f"VM '{name}' already exists. Use 'maqet apply {name}' to update, "
            f"or 'maqet rm {name}' to remove it first."
        )
    # ... rest of creation
```

**Effort**: Small (30 minutes)

---

### Issue #18: No Health Check for QEMU Binary

**Location**: `maqet/machine.py:493-513`
**Category**: MAINTAIN
**Problem**: `_pre_start_validation()` only checks if binary exists, not if it works:

```python
if not Path(binary).exists():
    raise MachineError(f"QEMU binary not found: {binary}")
```

**Recommendation**: Add health check:

```python
def _validate_qemu_binary(self, binary):
    """Validate QEMU binary exists and works."""
    if not Path(binary).exists():
        raise MachineError(f"QEMU binary not found: {binary}")

    # Quick health check: run qemu --version
    try:
        result = subprocess.run(
            [binary, "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            raise MachineError(f"QEMU binary failed health check: {binary}")

        LOG.debug(f"QEMU version: {result.stdout.splitlines()[0]}")
    except subprocess.TimeoutExpired:
        LOG.warning(f"QEMU binary health check timed out: {binary}")
```

**Effort**: Small (1 hour)

---

## Low Priority Issues (Technical Debt)

### Issue #19: Daemon Architecture Removed, Comments Remain

**Location**: `maqet/machine.py:129-158`
**Category**: MAINTAIN
**Problem**: Long architectural comment references daemon mode (was implemented, then removed). Comment is now outdated.

**Recommendation**: Update comment to reflect current state and future plans:

```python
# ARCHITECTURAL LIMITATION: Cross-process QMP Communication
# =======================================================
# Current Status: QMP only works in Python API mode (same process)
#
# Planned Fix for v1.0: Direct socket communication
# Planned Fix for v2.0: Optional daemon mode
#
# See Issue #1 in ARCHITECTURAL_REVIEW.md for details.
```

**Effort**: Small (15 minutes)

---

### Issue #20: No Metrics/Telemetry for Performance Monitoring

**Location**: N/A (missing feature)
**Category**: MAINTAIN
**Problem**: No way to track:

- VM start/stop times
- Snapshot operation durations
- QMP command latencies
- Database query performance

**Recommendation**: Add optional metrics:

```python
# metrics.py
from contextlib import contextmanager
import time

@contextmanager
def track_operation(operation_name):
    """Track operation duration."""
    start = time.time()
    try:
        yield
    finally:
        duration = time.time() - start
        LOG.debug(f"{operation_name} took {duration:.2f}s")
        # Optionally send to metrics backend (Prometheus, etc.)
```

**Effort**: Medium (2-3 days for comprehensive instrumentation)

---

### Issue #21: Test Naming Inconsistency

**Location**: `tests/` (multiple files)
**Category**: TEST
**Problem**: Test method names inconsistent:

- Some: `test_create_vm_success()`
- Others: `test_vm_creation()`
- Others: `test_that_vm_is_created()`

**Recommendation**: Standardize on pattern:

```
test_<method>_<scenario>_<expected>()

Examples:
test_add_with_valid_config_creates_vm()
test_start_without_config_raises_error()
test_snapshot_with_large_disk_completes_within_timeout()
```

**Effort**: Small (1-2 hours, can be automated with script)

---

### Issue #22: No Documentation for Adding New Storage Types

**Location**: `maqet/storage.py` (missing docs)
**Category**: MAINTAIN
**Problem**: Plugin architecture for storage devices exists (@storage_device decorator) but no documentation on how to add new types.

**Recommendation**: Add docstring with example:

```python
"""
Unified Storage Management System

...existing docs...

Adding New Storage Types
========================

1. Create class inheriting from BaseStorageDevice:

   class NVMeStorageDevice(BaseStorageDevice):
       def get_type(self) -> str:
           return "nvme"

       def supports_snapshots(self) -> bool:
           return False

       def get_qemu_args(self) -> List[str]:
           return ["-drive", f"file={self.file_path},if=nvme"]

       def create_if_needed(self) -> None:
           # Implementation...

2. Register the device type:

   StorageManager.register_device_type("nvme", NVMeStorageDevice)

3. Use in YAML configs:

   storage:
     - name: fast-disk
       type: nvme
       file: /path/to/nvme.img
       size: 500G
"""
```

**Effort**: Small (1 hour)

---

### Issue #23: No Performance Tests

**Location**: `tests/` (missing)
**Category**: TEST
**Problem**: Test suite has unit/integration/e2e tests, but no performance benchmarks for:

- VM start time
- Snapshot creation/loading speed
- Database query performance under load
- CLI command execution time

**Recommendation**: Add performance test suite:

```python
# tests/performance/test_vm_lifecycle_perf.py
import pytest
import time

@pytest.mark.performance
def test_vm_start_time_under_5_seconds(temp_maqet):
    """VM should start in less than 5 seconds."""
    vm_id = temp_maqet.add(config="minimal.yaml")

    start = time.time()
    temp_maqet.start(vm_id)
    duration = time.time() - start

    assert duration < 5.0, f"VM start took {duration:.2f}s (expected <5s)"
```

**Effort**: Medium (2-3 days)

---

## Positive Patterns (What's Done Well)

### Excellent Decorator-Based API System

The `@api_method` decorator system is **brilliant**. It enables:

- Single source of truth for methods
- Automatic CLI generation
- Automatic API generation
- Consistent help text and documentation
- Type-safe parameters

**Example from `maqet/maqet.py`**:

```python
@api_method(
    cli_name="start",
    description="Start a virtual machine",
    category="vm",
    requires_vm=True,
    examples=["maqet start myvm"],
)
def start(self, vm_id: str) -> VMInstance:
    """Implementation..."""
```

This pattern should be **preserved and expanded** in future development.

---

### Plugin Architecture for Storage Devices

The storage system uses a **registry pattern** with excellent extensibility:

```python
class StorageManager:
    _device_types: Dict[str, Type[BaseStorageDevice]] = {
        "qcow2": QCOW2StorageDevice,
        "raw": RawStorageDevice,
        "virtfs": VirtFSStorageDevice,
    }

    @classmethod
    def register_device_type(cls, type_name: str, device_class: Type[BaseStorageDevice]):
        cls._device_types[type_name.lower()] = device_class
```

This allows adding new storage types without modifying core code. **Exemplary design**.

---

### Configuration Handler System

The `@config_handler` decorator provides clean separation:

```python
@config_handler("memory")
def handle_memory(self, memory: str):
    if hasattr(self, "_qemu_machine") and self._qemu_machine:
        self._qemu_machine.add_args("-m", memory)
```

Each config key has dedicated handler. **Easy to extend and maintain**.

---

### Comprehensive Test Coverage

- **Test-to-code ratio: 2.4:1** (13,580 lines of tests for 5,639 lines of code)
- **Multiple test levels**: unit, integration, e2e, meta
- **Meta-tests** validate test quality (test_test_cleanup.py, test_test_isolation.py)
- **Good isolation**: Most tests use temp directories

**This is professional-grade testing**.

---

### XDG Base Directory Compliance

The `XDGDirectories` class properly separates:

- Data: `~/.local/share/maqet/` (VM definitions, database)
- Runtime: `/run/user/1000/maqet/` (sockets, PIDs)
- Config: `~/.config/maqet/` (templates)

**Follows Linux standards** for proper system integration.

---

### Clear Error Messages

Many error messages are **excellent**:

```python
raise MachineError(
    f"QEMU binary not found: {binary}. "
    f"Install QEMU or provide correct binary path."
)
```

Tells user:

1. What went wrong
2. How to fix it

**Keep this pattern**.

---

## Architectural Recommendations

### 1. Adopt Hexagonal Architecture (Ports and Adapters)

**Current State**: Mixed responsibilities (business logic + infrastructure)

**Recommendation**: Separate core domain from infrastructure:

```
maqet/
├── domain/           # Pure business logic (no I/O)
│   ├── vm.py         # VM entity
│   ├── snapshot.py   # Snapshot entity
│   └── ports/        # Interfaces
│       ├── vm_repository.py
│       └── qmp_client.py
├── infrastructure/   # Adapters implementing ports
│   ├── sqlite_vm_repository.py
│   ├── qemu_qmp_client.py
│   └── filesystem_storage.py
├── application/      # Use cases/services
│   ├── vm_lifecycle.py
│   └── snapshot_management.py
└── interfaces/       # CLI, API entry points
    ├── cli.py
    └── python_api.py
```

**Benefits**:

- Testable without infrastructure (mock repositories)
- Can swap SQLite for PostgreSQL easily
- Clear separation of concerns

**Effort**: Very large (3-4 weeks), but improves maintainability long-term.

---

### 2. Implement Command Pattern for Undo/Redo

**Use Case**: Users often want to undo VM configuration changes or snapshot operations.

**Recommendation**:

```python
class Command(ABC):
    @abstractmethod
    def execute(self): ...

    @abstractmethod
    def undo(self): ...

class CreateVMCommand(Command):
    def execute(self):
        self.vm_id = state_manager.create_vm(...)

    def undo(self):
        state_manager.remove_vm(self.vm_id)

# Usage
command_history = []
cmd = CreateVMCommand(name="test", config=...)
cmd.execute()
command_history.append(cmd)

# Later: undo
command_history[-1].undo()
```

**Effort**: Medium (3-5 days)

---

### 3. Add Event System for Extensibility

**Current**: No way for external code to hook into maqet events.

**Recommendation**: Implement observer pattern:

```python
class VMEventBus:
    def on(self, event_name, handler):
        """Register event handler."""

    def emit(self, event_name, **data):
        """Emit event to all handlers."""

# Usage
event_bus.on("vm.started", lambda vm: LOG.info(f"VM {vm.name} started"))
event_bus.on("vm.started", send_metrics_to_prometheus)
event_bus.on("vm.failed", alert_ops_team)

# In Maqet.start():
self.event_bus.emit("vm.started", vm=vm)
```

**Benefits**:

- Plugins can extend behavior
- Monitoring/metrics integration
- Workflow automation

**Effort**: Medium (2-3 days)

---

### 4. Refactoring Strategy (Incremental)

**Don't rewrite everything at once**. Use **Strangler Fig** pattern:

1. **Phase 1** (Week 1-2): Extract managers from Maqet class
   - VMManager, QMPManager, SnapshotCoordinator
   - Maqet becomes facade delegating to managers
   - All tests still pass

2. **Phase 2** (Week 3-4): Fix critical issues
   - Direct QMP socket communication
   - Standardize error handling
   - Fix global registries

3. **Phase 3** (Week 5-6): Improve quality
   - Extract long methods
   - Add centralized defaults
   - Performance tests

4. **Phase 4** (Month 2+): Long-term improvements
   - Hexagonal architecture
   - Event system
   - Daemon mode (2.0 feature)

---

## Test Quality Assessment

### Overall Assessment: **Excellent**

**Strengths**:

- **High coverage**: 2.4:1 test-to-code ratio
- **Multiple test levels**: unit, integration, e2e
- **Meta-tests**: Tests that validate test quality
- **Good isolation**: Most tests use temp directories
- **Realistic fixtures**: VM configs mirror real usage

**Weaknesses**:

1. **Some integration tests are actually e2e tests**
   - Example: `test_real_qemu_e2e.py` starts real QEMU (integration dir)
   - Should be in `tests/e2e/`

2. **Missing performance tests**
   - No benchmarks for VM start time
   - No snapshot operation benchmarks
   - No database query performance tests

3. **Test fixture duplication**
   - Similar fixtures in unit/integration/e2e conftest.py
   - Should be centralized in root conftest.py

4. **Some tests are fragile**
   - Example: Tests that depend on specific QEMU version output
   - Should mock qemu-img output format

5. **Missing negative test cases**
   - More tests needed for error conditions
   - Edge cases (disk full, permission denied, etc.)

### Test Coverage Gaps

Based on code review, these paths lack test coverage:

1. **Error Recovery**:
   - Database corruption recovery
   - Partial file cleanup after failed storage creation
   - QMP timeout handling

2. **Concurrency**:
   - Multiple processes creating VMs simultaneously
   - Concurrent snapshot operations on same drive
   - Database lock contention under load

3. **Edge Cases**:
   - VM with 1000+ storage devices
   - Snapshot name with special characters
   - Config file with recursive includes (if supported)

4. **Security**:
   - Config file with world-writable permissions
   - VirtFS sharing dangerous system paths
   - PID ownership validation with malicious PID

### Missing Test Scenarios

**Recommended new tests**:

```python
# tests/integration/test_concurrency.py
def test_concurrent_vm_creation_no_conflicts():
    """10 processes creating VMs simultaneously should succeed."""
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(create_vm, f"vm-{i}") for i in range(10)]
        results = [f.result() for f in futures]

    assert len(set(results)) == 10  # All unique VM IDs

# tests/integration/test_error_recovery.py
def test_recovery_from_database_corruption():
    """System should detect and offer to repair corrupted database."""
    # Corrupt database
    corrupt_database(state_manager.xdg.database_path)

    # Should detect corruption and offer recovery
    with pytest.raises(StateManagerError, match="database corrupt"):
        state_manager.list_vms()

# tests/security/test_security_validation.py
def test_virtfs_refuses_dangerous_paths():
    """VirtFS should refuse to share /etc or other system paths."""
    config = {"type": "virtfs", "path": "/etc", "mount_tag": "shared"}

    with pytest.raises(ValueError, match="dangerous system path"):
        VirtFSStorageDevice(config, "test-vm", 0)
```

---

## Summary by Module

| Module | Size (lines) | Health | Critical Issues | Notes |
|--------|--------------|--------|-----------------|-------|
| `maqet.py` | 1,496 | ⚠️ Yellow | God object (#2) | Needs refactoring into managers |
| `machine.py` | 907 | ⚠️ Yellow | Too many responsibilities (#4) | Extract QMPClient, ConfigValidator |
| `state.py` | 894 | ✅ Green | None | Well-structured, good practices |
| `storage.py` | 731 | ✅ Green | None | Excellent plugin architecture |
| `config_handlers.py` | 542 | ⚠️ Yellow | Complex _format_nested_value (#13) | Refactor long method |
| `snapshot.py` | 457 | ⚠️ Yellow | Synchronous operations (#7) | Add async support later |
| `cli_generator.py` | 625 | ⚠️ Yellow | Duplicate code (#10) | Extract common method |
| `config/parser.py` | 199 | ✅ Green | None | Clean, focused |
| `api/decorators.py` | 185 | ✅ Green | Global registry (#5) | Make instance-based |

**Legend**:

- ✅ **Green**: No critical issues, good architecture
- ⚠️ **Yellow**: Has issues but functional
- 🔴 **Red**: Critical problems, needs immediate attention

---

## Priority Roadmap

### Must Fix for 1.0 Release (Critical)

1. **Issue #1**: QMP cross-process communication (direct socket approach)
2. **Issue #2**: Refactor Maqet god object into managers

### Should Fix for 1.0 (High Priority)

3. **Issue #3**: Standardize error handling
4. **Issue #4**: Extract Machine class responsibilities
5. **Issue #5**: Fix global registry state
6. **Issue #6**: Improve SQLite connection management

### Can Defer to 1.1+ (Medium/Low Priority)

7. **Issue #7**: Async snapshot operations
8. **Issues #10-18**: Code quality improvements
9. **Issues #19-23**: Technical debt cleanup

---

## Conclusion

The maqet codebase demonstrates **strong architectural fundamentals** with innovative patterns (unified API system, plugin architecture). However, **two critical issues must be addressed before 1.0 release**:

1. Cross-process QMP communication (architectural limitation)
2. God object pattern in Maqet class (maintainability concern)

The recommended approach is **incremental refactoring** using the Strangler Fig pattern over 1-2 months:

- **Month 1**: Fix critical issues (#1, #2), address high-priority problems
- **Month 2**: Improve code quality, add performance tests
- **Month 3+**: Long-term architectural improvements (hexagonal architecture, events)

With these improvements, maqet will have a **solid foundation for long-term growth** and maintenance.

---

**Total Time Estimate**:

- Critical fixes: 3-4 weeks
- High priority: 2-3 weeks
- Medium/Low priority: 2-3 weeks
- **Total: 7-10 weeks** for comprehensive improvements

**Recommendation**: Start with critical issues immediately, defer low-priority items to post-1.0 releases.
