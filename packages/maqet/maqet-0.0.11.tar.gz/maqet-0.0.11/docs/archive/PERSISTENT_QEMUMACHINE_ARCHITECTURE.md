# Persistent QEMUMachine Architecture Analysis

**Date**: 2025-10-11
**Author**: Claude Code
**Purpose**: Explore architecture where QEMUMachine instances persist in background process, CLI communicates via IPC

---

## Executive Summary

**Proposed Architecture**: QEMUMachine instances live in persistent Python process, CLI communicates via IPC to call QEMUMachine methods remotely.

**Verdict**: **CAN BE ACHIEVED** with careful design. This is essentially a "mandatory daemon" architecture where ALL VM operations go through a persistent manager process.

**Key Insight**: Previous daemon implementation failed due to **mixed-mode problem** (some VMs started directly, some via daemon). Solution is to make daemon **mandatory and transparent** - auto-start on first use, all operations routed through it.

**Recommended Approach**: Hybrid architecture with automatic daemon lifecycle management.

---

## Table of Contents

1. [The Vision](#1-the-vision)
2. [Why This Makes Sense](#2-why-this-makes-sense)
3. [Architectural Options](#3-architectural-options)
4. [Detailed Analysis: Mandatory Daemon](#4-detailed-analysis-mandatory-daemon)
5. [IPC Technology Comparison](#5-ipc-technology-comparison)
6. [Implementation Strategy](#6-implementation-strategy)
7. [Challenges and Solutions](#7-challenges-and-solutions)
8. [Migration Path](#8-migration-path)
9. [Alternatives Analysis](#9-alternatives-analysis)
10. [Recommendation](#10-recommendation)

---

## 1. The Vision

### User's Architectural Requirements

```
┌────────────────────────────────────────┐
│ Persistent Python Process              │
│ "maqet-manager" (background)           │
│                                        │
│  ├─ Maqet() instance                   │
│  │   ├─ _machines = {                  │
│  │   │     "vm1": QEMUMachine(vm1),    │ ← Alive, holds QMP socket
│  │   │     "vm2": QEMUMachine(vm2)     │ ← Alive, holds QMP socket
│  │   │   }                             │
│  │   └─ StateManager, StorageManager   │
│  │                                     │
│  └─ IPC Server (DBus/gRPC/Socket)      │ ← Listens for CLI requests
└────────────────────────────────────────┘
            ↑ IPC Communication
┌────────────────────────────────────────┐
│ CLI Process (ephemeral)                │
│ "maqet start vm1"                      │
│                                        │
│  ├─ Detects manager running             │
│  ├─ Connects to IPC                     │
│  ├─ Sends: start("vm1", config)         │
│  ├─ Manager: creates QEMUMachine(vm1)   │
│  ├─ Receives: success/failure           │
│  └─ CLI exits                           │ ← Process dies, but VM lives
└────────────────────────────────────────┘
            ↑ IPC Communication
┌────────────────────────────────────────┐
│ CLI Process (ephemeral)                │
│ "maqet qmp vm1 query-status"           │
│                                        │
│  ├─ Connects to IPC                     │
│  ├─ Sends: qmp("vm1", "query-status")   │
│  ├─ Manager: _machines["vm1"].qmp(...)  │ ← Uses existing QEMUMachine
│  ├─ Receives: QMP response              │
│  └─ CLI exits                           │
└────────────────────────────────────────┘
```

**Key Properties**:

1. **QEMUMachine persistence**: Objects stay alive across CLI invocations
2. **Process independence**: Manager process lifecycle independent of CLI
3. **Method invocation**: CLI calls QEMUMachine methods via IPC
4. **QMP socket preservation**: File descriptors never cross process boundaries
5. **Transparent to user**: User doesn't manage daemon explicitly

---

## 2. Why This Makes Sense

### Advantages of Persistent QEMUMachine

#### A. QEMUMachine Features We Keep

The QEMUMachine class (from qemu/python/qemu/machine/machine.py) provides:

```python
class QEMUMachine:
    def __init__(self, binary, args=None):
        self._qmp_connection = None      # QMP socket connection
        self._qemu_process = None        # Popen instance
        self._monitor_address = None     # QMP socket path

    def launch(self):
        """Start QEMU process, establish QMP connection"""

    def shutdown(self):
        """Clean shutdown via QMP quit command"""

    def qmp(self, cmd, **kwargs):
        """Execute QMP command on live connection"""

    def wait(self):
        """Wait for QEMU process to exit"""

    def get_pid(self):
        """Get QEMU process PID"""
```

**Benefits we preserve**:

- ✅ QMP connection management (handshake, capabilities negotiation)
- ✅ Process lifecycle tracking (Popen, wait, returncode)
- ✅ Clean shutdown coordination (QMP quit → wait for exit)
- ✅ Error handling (QMP protocol errors, connection drops)
- ✅ Event monitoring (QMP events stream)
- ✅ Logging and debugging (QEMUMachine logs)

#### B. What We Gain

**1. True Cross-Invocation State**

```bash
maqet start vm1        # QEMUMachine(vm1) created, stays alive
maqet qmp vm1 status   # Uses same QEMUMachine instance
maqet keys vm1 ctrl-c  # Uses same QMP connection
maqet stop vm1         # Clean shutdown via QEMUMachine.shutdown()
```

**2. Advanced Features Possible**

- **Event monitoring**: Daemon watches QMP events, triggers actions
- **Automatic recovery**: Detect QEMU crashes, restart if configured
- **Performance monitoring**: Track CPU/memory usage continuously
- **Background tasks**: Periodic screenshots, log collection
- **Stateful workflows**: Multi-step automation (boot → wait → login → commands)

**3. Consistency**

- **Single source of truth**: One Maqet instance manages all VMs
- **No mixed modes**: All operations go through same code path
- **Transaction safety**: Multiple CLI commands don't race

---

## 3. Architectural Options

### Option A: Mandatory Daemon with Auto-Start (RECOMMENDED)

**Concept**: Daemon is required but starts automatically, user never manages it manually.

```python
# CLI entry point (maqet/__main__.py)
def main():
    # Check if daemon is running
    if not is_daemon_running():
        # Auto-start daemon transparently
        start_daemon_background()
        wait_for_daemon_ready(timeout=5)

    # All commands go through daemon
    client = get_daemon_client()
    result = client.call_method(command, args)
    return result
```

**User Experience**:

```bash
maqet start vm1        # Daemon auto-starts (first invocation)
                       # VM started via daemon
                       # "Starting maqet manager..." (one-time message)

maqet qmp vm1 status   # Daemon already running
                       # Command routed instantly

maqet stop vm1         # Daemon still running (manages cleanup)
```

**Daemon Lifecycle**:

- **Start**: Automatically on first maqet command
- **Stop**: Never (runs until logout) OR idle timeout (30 min no VMs)
- **Restart**: Automatically if crash detected

---

### Option B: Explicit Daemon with Manual Management

**Concept**: User explicitly starts/stops daemon, CLI errors if daemon not running.

```bash
maqet daemon start     # User must start daemon
maqet start vm1        # Works (daemon running)
maqet daemon stop      # Stops daemon, kills all VMs
```

**Pros**:

- Simple implementation
- Clear daemon state (running/stopped)

**Cons**:

- ❌ Poor UX (users forget to start daemon)
- ❌ Confusing error messages ("daemon not running")
- ❌ Inconsistent behavior (CLI works differently if daemon down)

**Verdict**: Not recommended - UX too poor.

---

### Option C: Hybrid - Direct Mode + Optional Daemon

**Concept**: CLI works directly by default, daemon is optional for advanced features.

```bash
# Direct mode (default)
maqet start vm1        # Works without daemon (limited QMP)

# Daemon mode (opt-in)
maqet daemon start     # Enable advanced features
maqet start vm2        # Routed to daemon (full QMP)
```

**Pros**:

- No breaking changes (direct mode still works)
- Advanced users can opt-in to daemon

**Cons**:

- ❌ Mixed-mode problem returns
- ❌ Two code paths to maintain
- ❌ Confusing which VMs have which features

**Verdict**: Possible but complex, defeats purpose of persistent QEMUMachine.

---

### Option D: Unix Socket FD Passing (Advanced)

**Concept**: CLI starts VM, passes QMP socket file descriptor to daemon.

```python
# CLI starts QEMU directly
machine = QEMUMachine(binary, args)
machine.launch()

# Pass FD to daemon via Unix socket (SCM_RIGHTS)
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.connect('/run/user/1000/maqet/daemon.sock')
send_fd(sock, machine._qmp_connection.fileno())

# Daemon receives FD, reconstructs QMP connection
```

**Pros**:

- Keep direct start capability
- Transfer ownership to daemon

**Cons**:

- ❌ Very complex (FD passing, connection reconstruction)
- ❌ Platform-specific (Linux/BSD only)
- ❌ Fragile (state transfer, error-prone)
- ❌ QEMUMachine state transfer difficult (Popen, internal state)

**Verdict**: Technically possible but extremely complex, high risk.

---

## 4. Detailed Analysis: Mandatory Daemon

### 4.1 Architecture Components

#### Component 1: Manager Process (maqet-manager)

**File**: `maqet/manager_daemon.py`

```python
class MaqetManagerDaemon:
    """Persistent process managing all QEMUMachine instances."""

    def __init__(self):
        self.maqet = Maqet()  # Single persistent instance
        self.ipc_server = None  # DBus/gRPC server
        self.running = True

    def start(self):
        """Initialize daemon, start IPC server, event loop."""
        self._setup_signal_handlers()
        self._setup_ipc_server()
        self._load_running_vms()  # Recover VMs from DB
        self._run_event_loop()

    def _run_event_loop(self):
        """Main loop: handle IPC requests, monitor VMs."""
        while self.running:
            # Handle IPC requests (non-blocking)
            self._process_ipc_requests()

            # Monitor running VMs
            self._check_vm_health()

            # Idle timeout (optional)
            if self._should_shutdown():
                break

            time.sleep(0.1)

    def handle_request(self, method_name, args, kwargs):
        """Execute Maqet method, return result."""
        method = getattr(self.maqet, method_name)
        try:
            result = method(*args, **kwargs)
            return {"status": "success", "result": result}
        except Exception as e:
            return {"status": "error", "error": str(e)}
```

**Lifecycle**:

```
[Boot] → [Idle] → [First CLI call] → [Auto-start] → [Running] → [Idle timeout] → [Shutdown]
                                           ↓
                                    [Handle requests]
                                           ↓
                                    [VMs running] → [No timeout]
```

---

#### Component 2: IPC Server (in daemon)

**File**: `maqet/ipc/server.py`

```python
class IPCServer:
    """Abstract IPC server (DBus/gRPC/Unix socket implementation)."""

    def __init__(self, handler_callback):
        self.handler = handler_callback  # MaqetManagerDaemon.handle_request

    def start(self):
        """Start listening for requests."""
        raise NotImplementedError

    def stop(self):
        """Stop server gracefully."""
        raise NotImplementedError

    def wait_for_request(self, timeout=0.1):
        """Non-blocking request check."""
        raise NotImplementedError
```

**Implementations**:

- `DBusIPCServer` - Use pydbus (current dbus_service.py)
- `GRPCIPCServer` - Use grpc library
- `UnixSocketIPCServer` - Raw Unix domain socket

---

#### Component 3: CLI Client (transparent proxy)

**File**: `maqet/ipc/client.py`

```python
class MaqetClient:
    """Transparent proxy to daemon, looks like local Maqet."""

    def __init__(self):
        self._ensure_daemon_running()
        self.connection = self._connect_to_daemon()

    def _ensure_daemon_running(self):
        """Auto-start daemon if not running."""
        if not self._is_daemon_running():
            self._start_daemon()
            self._wait_for_ready(timeout=5)

    def _is_daemon_running(self):
        """Check PID file, test connection."""
        pid_file = Path("/run/user") / str(os.getuid()) / "maqet" / "manager.pid"
        if not pid_file.exists():
            return False

        pid = int(pid_file.read_text())
        return psutil.pid_exists(pid)

    def _start_daemon(self):
        """Fork daemon process."""
        # Option 1: Double fork daemonization
        # Option 2: systemd user service (systemd-run)
        # Option 3: subprocess.Popen with detach

    def __getattr__(self, name):
        """Proxy method calls to daemon."""
        def method_proxy(*args, **kwargs):
            return self._call_remote_method(name, args, kwargs)
        return method_proxy

    def _call_remote_method(self, method_name, args, kwargs):
        """Send IPC request, wait for response."""
        request = {
            "method": method_name,
            "args": args,
            "kwargs": kwargs
        }
        response = self.connection.send_request(request)

        if response["status"] == "error":
            raise MaqetError(response["error"])
        return response["result"]
```

**Usage in CLI**:

```python
# maqet/__main__.py
def main():
    # Old code (direct):
    # maqet = Maqet()

    # New code (via daemon):
    maqet = MaqetClient()  # Looks identical, but proxies to daemon

    # All method calls work transparently
    maqet.start("vm1")
    result = maqet.qmp("vm1", "query-status")
```

---

### 4.2 Daemon Auto-Start Strategy

#### Strategy 1: Double Fork Daemonization (Traditional)

```python
def _start_daemon_double_fork():
    """Classic Unix daemonization."""

    # First fork - parent exits, child becomes session leader
    pid = os.fork()
    if pid > 0:
        # Parent process - wait for daemon to be ready
        wait_for_daemon_ready()
        return

    # Child process - detach from terminal
    os.setsid()

    # Second fork - prevent acquiring controlling terminal
    pid = os.fork()
    if pid > 0:
        sys.exit(0)  # First child exits

    # Grandchild - this becomes the daemon
    os.chdir("/")
    os.umask(0)

    # Close standard file descriptors
    sys.stdin.close()
    sys.stdout = open("/dev/null", "w")
    sys.stderr = open("/dev/null", "w")

    # Write PID file
    pid_file = Path("/run/user") / str(os.getuid()) / "maqet" / "manager.pid"
    pid_file.write_text(str(os.getpid()))

    # Start daemon
    daemon = MaqetManagerDaemon()
    daemon.start()
```

**Pros**:

- ✅ Traditional, well-understood
- ✅ Works on all Unix systems
- ✅ No external dependencies

**Cons**:

- ❌ Complex implementation
- ❌ No automatic restart on crash
- ❌ No systemd integration

---

#### Strategy 2: systemd User Service (Modern Linux)

```python
def _start_daemon_systemd():
    """Start daemon as systemd user service."""

    # Use systemd-run to start transient service
    subprocess.run([
        "systemd-run",
        "--user",              # User service (not system)
        "--unit=maqet-manager", # Service name
        "--description=Maqet VM Manager",
        "--remain-after-exit", # Keep service active
        sys.executable,        # Python interpreter
        "-m", "maqet.manager_daemon"  # Module to run
    ], check=True)

    # Wait for daemon to be ready
    wait_for_daemon_ready()
```

**Unit file** (optional, for persistent service):

```ini
# ~/.config/systemd/user/maqet-manager.service
[Unit]
Description=Maqet VM Manager
After=dbus.service

[Service]
Type=simple
ExecStart=/usr/bin/python3 -m maqet.manager_daemon
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

**Pros**:

- ✅ systemd handles daemonization
- ✅ Automatic restart on crash
- ✅ Clean lifecycle management
- ✅ Journal logging (journalctl --user -u maqet-manager)
- ✅ User can manage: `systemctl --user status maqet-manager`

**Cons**:

- ❌ Linux-only (requires systemd)
- ❌ User must have systemd user session

---

#### Strategy 3: Hybrid (systemd preferred, fallback to fork)

```python
def _start_daemon():
    """Auto-detect best daemonization method."""

    # Try systemd first (if available)
    if _has_systemd_user_session():
        try:
            _start_daemon_systemd()
            return
        except Exception as e:
            LOG.warning(f"systemd start failed: {e}, falling back to fork")

    # Fallback to double fork
    _start_daemon_double_fork()

def _has_systemd_user_session():
    """Check if systemd user session is available."""
    # Check XDG_RUNTIME_DIR has systemd socket
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
    if not runtime_dir:
        return False

    systemd_sock = Path(runtime_dir) / "systemd" / "private"
    return systemd_sock.exists()
```

**Verdict**: This is the best approach - modern systems get systemd benefits, older systems still work.

---

### 4.3 IPC Communication Flow

#### Example: `maqet start vm1`

```
┌─────────────────────┐
│ CLI Process         │
│ maqet start vm1     │
└──────────┬──────────┘
           │
           │ 1. Check daemon running
           ├─────────────────────────────┐
           │                             │
           │ 2. Not running → auto-start │
           │    (systemd-run / fork)     │
           │                             │
           ↓                             ↓
┌─────────────────────────────────────────┐
│ Daemon Process (maqet-manager)          │
│                                         │
│  3. Daemon initializes:                 │
│     - Maqet() instance created          │
│     - IPC server starts                 │
│     - Signal handlers registered        │
│     - PID file written                  │
│                                         │
│  4. Ready for requests                  │
└──────────┬──────────────────────────────┘
           │
           │ 5. CLI connects (DBus/gRPC/Socket)
           │
┌──────────▼──────────┐
│ IPC Request         │
│ {                   │
│   method: "start",  │
│   args: ["vm1"],    │
│   kwargs: {}        │
│ }                   │
└──────────┬──────────┘
           │
           │ 6. Daemon receives request
           │
┌──────────▼──────────────────────────────┐
│ Daemon: MaqetManagerDaemon.handle_request│
│                                         │
│  7. Call method:                        │
│     self.maqet.start("vm1")             │
│                                         │
│  8. Maqet.start():                      │
│     - Load config from DB               │
│     - Create Machine(vm1)               │
│     - QEMUMachine.launch()              │
│     - Store Machine in self._machines   │
│     - Update VM status in DB            │
│                                         │
│  9. Return result                       │
└──────────┬──────────────────────────────┘
           │
           │ 10. IPC Response
           │
┌──────────▼──────────┐
│ IPC Response        │
│ {                   │
│   status: "success",│
│   result: {         │
│     vm_id: "vm1",   │
│     pid: 12345,     │
│     socket_path: ...│
│   }                 │
│ }                   │
└──────────┬──────────┘
           │
           │ 11. CLI receives result
           │
┌──────────▼──────────┐
│ CLI displays output │
│ "VM vm1 started"    │
│ PID: 12345          │
└─────────────────────┘

CLI exits → Daemon keeps running → QEMUMachine(vm1) alive
```

#### Example: `maqet qmp vm1 query-status`

```
┌─────────────────────┐
│ CLI Process         │
│ maqet qmp vm1 ...   │
└──────────┬──────────┘
           │
           │ 1. Check daemon running (already running)
           │ 2. Connect to IPC
           │
┌──────────▼──────────┐
│ IPC Request         │
│ {                   │
│   method: "qmp",    │
│   args: ["vm1",     │
│           "query-   │
│            status"] │
│ }                   │
└──────────┬──────────┘
           │
┌──────────▼──────────────────────────────┐
│ Daemon: MaqetManagerDaemon.handle_request│
│                                         │
│  3. Call method:                        │
│     self.maqet.qmp("vm1", "query-status")│
│                                         │
│  4. Maqet.qmp():                        │
│     machine = self._machines["vm1"]     │ ← QEMUMachine alive!
│     result = machine.qmp("query-status")│ ← Uses existing QMP socket
│     return result                       │
│                                         │
└──────────┬──────────────────────────────┘
           │
           │ 5. IPC Response
           │
┌──────────▼──────────┐
│ IPC Response        │
│ {                   │
│   status: "success",│
│   result: {         │
│     running: true,  │
│     status: "running│
│   }                 │
│ }                   │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│ CLI displays result │
│ Status: running     │
└─────────────────────┘
```

**Key Observation**: QEMUMachine instance persists in daemon, QMP socket never crosses process boundaries.

---

## 5. IPC Technology Comparison

### Option 1: DBus (Current Implementation)

**Technology**: D-Bus session bus (org.freedesktop.DBus)

**Library**: `pydbus` (current) or `dbus-python`

**Pros**:

- ✅ Already implemented (dbus_service.py)
- ✅ Standard on Linux desktop
- ✅ Automatic service activation (systemd integration)
- ✅ Type-safe method signatures
- ✅ Introspection (d-feet, busctl)
- ✅ Security (session bus = per-user)

**Cons**:

- ❌ Linux-only (no macOS/BSD support)
- ❌ Requires D-Bus daemon running
- ❌ Complex for simple use case
- ❌ Serialization overhead (XML marshalling)

**Example**:

```python
# Server (daemon)
from pydbus import SessionBus

class MaqetService:
    """<node>
        <interface name='com.maqet.Manager'>
            <method name='Start'>
                <arg type='s' name='vm_id' direction='in'/>
                <arg type='s' name='result' direction='out'/>
            </method>
        </interface>
    </node>"""

    def Start(self, vm_id):
        self.maqet.start(vm_id)
        return "success"

bus = SessionBus()
bus.publish("com.maqet.Manager", MaqetService())

# Client (CLI)
bus = SessionBus()
service = bus.get("com.maqet.Manager")
result = service.Start("vm1")
```

**Verdict**: Good for Linux-focused project, already implemented.

---

### Option 2: gRPC

**Technology**: Google RPC framework (HTTP/2 based)

**Library**: `grpcio` + `protobuf`

**Pros**:

- ✅ Cross-platform (Linux/macOS/BSD/Windows)
- ✅ High performance (binary protocol)
- ✅ Strong typing (protobuf schema)
- ✅ Streaming support (for logs, events)
- ✅ Mature, well-documented
- ✅ Bidirectional communication

**Cons**:

- ❌ Large dependency (grpcio + protobuf)
- ❌ Code generation required (protoc)
- ❌ More complex than needed
- ❌ HTTP/2 overhead for local IPC

**Example**:

```protobuf
// maqet.proto
syntax = "proto3";

service MaqetManager {
    rpc Start(StartRequest) returns (StartResponse);
    rpc Qmp(QmpRequest) returns (QmpResponse);
}

message StartRequest {
    string vm_id = 1;
}

message StartResponse {
    string status = 1;
    int32 pid = 2;
}
```

```python
# Server (daemon)
import grpc
from concurrent import futures
import maqet_pb2_grpc

class MaqetServicer(maqet_pb2_grpc.MaqetManagerServicer):
    def Start(self, request, context):
        result = self.maqet.start(request.vm_id)
        return StartResponse(status="success", pid=result.pid)

server = grpc.server(futures.ThreadPoolExecutor())
maqet_pb2_grpc.add_MaqetManagerServicer_to_server(MaqetServicer(), server)
server.add_insecure_port('unix:///run/user/1000/maqet/manager.sock')
server.start()

# Client (CLI)
channel = grpc.insecure_channel('unix:///run/user/1000/maqet/manager.sock')
stub = maqet_pb2_grpc.MaqetManagerStub(channel)
response = stub.Start(StartRequest(vm_id="vm1"))
```

**Verdict**: Overkill for this use case, but best for cross-platform.

---

### Option 3: Unix Domain Socket + JSON-RPC (RECOMMENDED)

**Technology**: Unix domain socket + JSON message protocol

**Library**: Built-in `socket` + `json`

**Pros**:

- ✅ Simplest implementation (no dependencies)
- ✅ Cross-platform (Unix socket on Linux/macOS/BSD)
- ✅ Low latency (no network stack)
- ✅ Secure (filesystem permissions)
- ✅ Easy debugging (JSON messages)
- ✅ Full control over protocol

**Cons**:

- ❌ Manual protocol design
- ❌ No automatic type checking
- ❌ No introspection tools

**Example**:

```python
# Server (daemon)
import socket
import json

sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.bind('/run/user/1000/maqet/manager.sock')
sock.listen(5)

while True:
    conn, _ = sock.accept()
    data = conn.recv(4096)
    request = json.loads(data)

    # Call method
    method = getattr(maqet, request["method"])
    result = method(*request["args"], **request["kwargs"])

    # Send response
    response = {"status": "success", "result": result}
    conn.sendall(json.dumps(response).encode())
    conn.close()

# Client (CLI)
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.connect('/run/user/1000/maqet/manager.sock')

request = {
    "method": "start",
    "args": ["vm1"],
    "kwargs": {}
}
sock.sendall(json.dumps(request).encode())

response = json.loads(sock.recv(4096))
print(response["result"])
```

**Verdict**: Best balance of simplicity, performance, and control.

---

### Recommendation: Unix Socket + JSON-RPC

**Reasoning**:

1. **Simplicity**: No external dependencies, easy to understand
2. **Performance**: Unix socket is fastest local IPC on Linux
3. **Portability**: Works on all Unix systems
4. **Debuggability**: JSON messages easy to inspect
5. **Maintainability**: Full control, no library versioning issues

**Fallback**: Keep DBus code for optional integration (systemd activation).

---

## 6. Implementation Strategy

### Phase 1: Core Daemon (Week 1)

**Tasks**:

1. Create `maqet/manager_daemon.py`:
   - `MaqetManagerDaemon` class
   - Event loop with request handling
   - Signal handlers (SIGTERM, SIGINT)
   - PID file management

2. Create `maqet/ipc/unix_socket_server.py`:
   - `UnixSocketIPCServer` class
   - JSON-RPC protocol handler
   - Non-blocking request processing

3. Create `maqet/ipc/client.py`:
   - `MaqetClient` class
   - Daemon detection and auto-start
   - Method proxying via `__getattr__`

**Deliverable**: Daemon can start, handle requests, CLI can connect.

---

### Phase 2: Auto-Start Mechanism (Week 1-2)

**Tasks**:

1. Implement daemon auto-start:
   - Detect systemd availability
   - `_start_daemon_systemd()` implementation
   - `_start_daemon_double_fork()` fallback
   - Wait-for-ready logic (poll PID file + test connection)

2. Create systemd user service template:
   - `maqet-manager.service` file
   - Installation script
   - Documentation

**Deliverable**: CLI auto-starts daemon transparently.

---

### Phase 3: Method Forwarding (Week 2)

**Tasks**:

1. Implement request serialization:
   - Handle arguments (JSON-serializable types)
   - Handle exceptions (serialize MaqetError)
   - Handle return values (dict, list, etc.)

2. Update CLI to use `MaqetClient`:
   - Modify `maqet/__main__.py`
   - Replace `Maqet()` with `MaqetClient()`
   - Test all commands work via daemon

**Deliverable**: All maqet commands work via daemon.

---

### Phase 4: State Recovery (Week 3)

**Tasks**:

1. Daemon startup recovery:
   - Load running VMs from database
   - Reconnect to QEMU processes (if QMP sockets exist)
   - Mark dead VMs as stopped

2. Handle daemon crash:
   - CLI detects stale PID
   - Auto-restart daemon
   - User notification ("daemon restarted")

**Deliverable**: Daemon survives restarts, recovers VM state.

---

### Phase 5: Advanced Features (Week 4)

**Tasks**:

1. Event monitoring:
   - QMP event stream handling
   - Event-triggered actions (SHUTDOWN → cleanup)
   - Event logging

2. Idle shutdown:
   - Configurable timeout (default: disabled)
   - Shutdown only if no VMs running
   - User can disable: `MAQET_DAEMON_PERSIST=1`

**Deliverable**: Production-ready daemon with advanced features.

---

### Phase 6: Testing & Documentation (Week 5)

**Tasks**:

1. Unit tests:
   - Daemon lifecycle
   - IPC communication
   - Auto-start logic
   - Error handling

2. Integration tests:
   - Full CLI workflow via daemon
   - Daemon crash recovery
   - Multi-client concurrency

3. Documentation:
   - Architecture document (this file)
   - User guide (daemon management)
   - Troubleshooting guide

**Deliverable**: Fully tested, documented daemon architecture.

---

## 7. Challenges and Solutions

### Challenge 1: Daemon Crash Handling

**Problem**: If daemon crashes, all QEMUMachine instances lost.

**Solutions**:

**A. Process Supervision (Recommended)**

```bash
# systemd automatically restarts daemon on crash
Restart=on-failure
RestartSec=5
```

**B. State Persistence**

```python
# Save VM state periodically
def _save_vm_state(self):
    """Persist VM state to disk (fallback if daemon crashes)."""
    for vm_id, machine in self._machines.items():
        state = {
            "vm_id": vm_id,
            "pid": machine.get_pid(),
            "socket_path": machine._monitor_address,
            "launched_at": machine._launched_at
        }
        # Save to ~/.local/share/maqet/state/vm1.json
```

**C. QMP Socket Reconnection**

```python
# On daemon restart, reconnect to existing QEMU processes
def _recover_running_vms(self):
    """Reconnect to VMs that were running when daemon crashed."""
    for vm in self.maqet.state_manager.list_vms():
        if vm.status == "running" and vm.pid:
            # Check if QEMU process still alive
            if psutil.pid_exists(vm.pid):
                # Try to reconnect to QMP socket
                try:
                    machine = self._reconnect_to_vm(vm)
                    self.maqet._machines[vm.id] = machine
                except Exception as e:
                    LOG.error(f"Failed to recover {vm.id}: {e}")
                    # Mark as stopped
                    self.maqet.state_manager.update_vm(vm.id, status="stopped")
```

**Verdict**: Combination of A + C is best - systemd restarts daemon, daemon recovers VMs.

---

### Challenge 2: Concurrent Access

**Problem**: Multiple CLI processes calling daemon simultaneously.

**Solution**: Thread-safe request handling.

```python
class MaqetManagerDaemon:
    def __init__(self):
        self.maqet_lock = threading.RLock()  # Reentrant lock

    def handle_request(self, method_name, args, kwargs):
        """Thread-safe method execution."""
        with self.maqet_lock:
            method = getattr(self.maqet, method_name)
            return method(*args, **kwargs)
```

**Alternative**: Single-threaded with request queue (simpler, sufficient).

```python
def _run_event_loop(self):
    """Process requests sequentially."""
    while self.running:
        request = self.ipc_server.get_next_request(timeout=0.1)
        if request:
            response = self._handle_request(request)
            request.send_response(response)
```

**Verdict**: Single-threaded is simpler and sufficient (maqet not designed for concurrency).

---

### Challenge 3: Serialization of Complex Types

**Problem**: Some return values are complex objects (VMInstance, pathlib.Path).

**Solution**: JSON-serializable conversion layer.

```python
def _serialize_result(result):
    """Convert result to JSON-serializable format."""
    if isinstance(result, VMInstance):
        return result.__dict__  # Dataclass → dict
    elif isinstance(result, Path):
        return str(result)
    elif isinstance(result, list):
        return [_serialize_result(item) for item in result]
    elif isinstance(result, dict):
        return {k: _serialize_result(v) for k, v in result.items()}
    else:
        return result  # Primitive type

def _deserialize_result(data, expected_type=None):
    """Convert JSON data back to Python objects."""
    if expected_type == VMInstance:
        return VMInstance(**data)
    elif expected_type == Path:
        return Path(data)
    # ... etc
    return data
```

**Verdict**: Explicit conversion layer in IPC client/server.

---

### Challenge 4: Daemon Not Starting

**Problem**: User has no systemd, fork fails, etc.

**Solution**: Comprehensive fallback chain + helpful error messages.

```python
def _ensure_daemon_running(self):
    """Try multiple strategies to start daemon."""
    if self._is_daemon_running():
        return

    # Strategy 1: systemd user service
    if _has_systemd():
        try:
            _start_daemon_systemd()
            if _wait_for_daemon_ready(timeout=5):
                return
        except Exception as e:
            LOG.warning(f"systemd start failed: {e}")

    # Strategy 2: Double fork
    try:
        _start_daemon_double_fork()
        if _wait_for_daemon_ready(timeout=5):
            return
    except Exception as e:
        LOG.warning(f"Fork start failed: {e}")

    # Strategy 3: Give up, provide helpful error
    raise MaqetError(
        "Failed to start maqet daemon. Please try:\n"
        "  1. Start manually: python3 -m maqet.manager_daemon\n"
        "  2. Check logs: journalctl --user -u maqet-manager\n"
        "  3. Report issue: https://github.com/..."
    )
```

---

### Challenge 5: Migration Path (Backward Compatibility)

**Problem**: Existing users have VMs, direct mode currently works.

**Solution**: Gradual migration with feature flag.

```python
# Phase 1: Optional daemon (default: disabled)
MAQET_USE_DAEMON = os.environ.get("MAQET_USE_DAEMON", "0") == "1"

if MAQET_USE_DAEMON:
    maqet = MaqetClient()  # Daemon mode
else:
    maqet = Maqet()  # Direct mode (legacy)

# Phase 2: Enable by default (with opt-out)
MAQET_USE_DAEMON = os.environ.get("MAQET_USE_DAEMON", "1") == "1"

# Phase 3: Remove direct mode (mandatory daemon)
maqet = MaqetClient()  # Always daemon
```

**Migration timeline**:

- Version 1.1: Optional daemon (opt-in)
- Version 1.2: Default daemon (opt-out)
- Version 2.0: Mandatory daemon (no direct mode)

---

## 8. Migration Path

### Version 1.1 - Optional Daemon (Opt-In)

**Changes**:

- Add `maqet/manager_daemon.py`
- Add `maqet/ipc/` module
- Environment variable: `MAQET_USE_DAEMON=1` to enable
- Default: Direct mode (no breaking changes)

**User Experience**:

```bash
# Old behavior (default)
maqet start vm1    # Direct mode, limited QMP

# New behavior (opt-in)
MAQET_USE_DAEMON=1 maqet start vm1   # Daemon mode, full QMP
```

**Documentation**: "New experimental daemon mode available, set MAQET_USE_DAEMON=1"

---

### Version 1.2 - Default Daemon (Opt-Out)

**Changes**:

- Flip default: `MAQET_USE_DAEMON=1` by default
- Add deprecation warning for direct mode
- Update documentation to recommend daemon

**User Experience**:

```bash
# New default
maqet start vm1    # Daemon mode (auto-starts transparently)

# Opt-out (if issues)
MAQET_USE_DAEMON=0 maqet start vm1   # Direct mode (deprecated)
```

**Documentation**: "Daemon mode now default, improved QMP support. Direct mode deprecated."

---

### Version 2.0 - Mandatory Daemon

**Changes**:

- Remove direct mode code paths
- Remove `MAQET_USE_DAEMON` environment variable
- CLI always uses `MaqetClient()`

**User Experience**:

```bash
maqet start vm1    # Always daemon mode (transparent)
```

**Documentation**: "All commands now use daemon architecture for consistent behavior."

---

## 9. Alternatives Analysis

### Alternative 1: Direct Socket QMP (No Daemon)

**Concept**: CLI connects directly to QMP socket stored in database.

**Why it doesn't meet requirements**:

- ❌ Loses QEMUMachine features (lifecycle, events, error handling)
- ❌ Duplicates QMP protocol logic
- ❌ No process tracking (QEMU crashes undetected)
- ❌ No advanced features (monitoring, automation)

**User's requirement**: "I want to keep [QEMUMachine] functionality" → This approach loses it.

---

### Alternative 2: QEMUMachine State Serialization

**Concept**: Serialize QEMUMachine state to disk, reload on each CLI invocation.

**Why it doesn't work**:

- ❌ Cannot serialize file descriptors (QMP socket)
- ❌ Cannot serialize Popen objects (QEMU process handle)
- ❌ Would need to reconstruct complex internal state
- ❌ Fragile, high risk of state corruption

**Technical barrier**: Python's `pickle` cannot serialize OS-level resources.

---

### Alternative 3: Stateless CLI + QMP Library

**Concept**: CLI is stateless, uses QMP library (qemu.qmp) directly.

**Why it doesn't meet requirements**:

- ❌ No QEMUMachine instance → loses lifecycle management
- ❌ Manual QMP connection management in every command
- ❌ No process tracking, no event handling
- ❌ Significantly more complex CLI code

**User's requirement**: "Running instance should stay inside QEMUMachine" → This approach removes it.

---

## 10. Recommendation

### Summary: Mandatory Daemon with Auto-Start (RECOMMENDED)

**Architecture**: All VM operations go through persistent daemon process, CLI auto-starts daemon transparently.

**Key Design Decisions**:

1. **IPC Protocol**: Unix domain socket + JSON-RPC
   - Simplest, no dependencies, full control
   - Fallback: Keep DBus for systemd integration

2. **Daemon Lifecycle**: Auto-start with systemd (preferred) or double-fork (fallback)
   - User never manages daemon manually
   - Transparent experience

3. **Method Proxying**: `MaqetClient` proxies all methods to daemon
   - CLI code unchanged (just swap `Maqet()` for `MaqetClient()`)
   - Type-safe (no API changes)

4. **State Recovery**: Daemon reconnects to running VMs on restart
   - Uses PID + QMP socket path from database
   - systemd restarts daemon on crash

5. **Migration Path**: Gradual rollout (1.1 opt-in → 1.2 default → 2.0 mandatory)
   - No breaking changes initially
   - Time for user feedback and bug fixes

**Implementation Timeline**:

- **Week 1**: Core daemon + IPC server
- **Week 2**: Auto-start mechanism + method forwarding
- **Week 3**: State recovery + crash handling
- **Week 4**: Advanced features (events, monitoring)
- **Week 5**: Testing + documentation

**Total Effort**: 5 weeks for complete implementation.

---

## Conclusion

**Can this be achieved?** **YES**, with careful implementation of mandatory daemon architecture.

**Why it works**:

- QEMUMachine instances live in persistent process ✅
- CLI communicates via IPC (Unix socket + JSON-RPC) ✅
- QMP sockets never cross process boundaries ✅
- All QEMUMachine features preserved ✅
- Transparent to user (auto-start) ✅

**Why previous daemon failed**: Mixed-mode problem (direct + daemon starts).

**Solution**: Make daemon mandatory and transparent - user never thinks about it, but it's always there managing VMs.

**Key to success**: Auto-start + transparent proxying + state recovery.

This architecture achieves your vision: **"Running instance of QEMU VM should stay inside QEMUMachine instance"** while providing excellent user experience through transparent daemon management.
