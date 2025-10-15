# Per-VM Process Architecture (No Daemon)

**Date**: 2025-10-11
**Status**: **IMPLEMENTED** (as of 2025-10-10)
**Author**: Claude Code

---

## Executive Summary

**Current Architecture**: Each VM runs in its own persistent Python process (VM Runner) that manages QEMUMachine instance. CLI communicates with individual VM runner processes via IPC.

**Key Insight**: Why have a daemon managing all VMs when each VM can manage itself? One VM = One VM Runner process = One QEMUMachine instance.

**Verdict**: **SUPERIOR ARCHITECTURE** - simpler, more robust, no single point of failure, natural lifecycle, DB is source of truth.

**No daemon needed**: Each VM runner process is independent, CLI finds them via PID in database.

---

## Table of Contents

1. [The Architecture](#1-the-architecture)
2. [Why This Is Better](#2-why-this-is-better)
3. [Component Design](#3-component-design)
4. [Process Lifecycle](#4-process-lifecycle)
5. [Database Schema](#5-database-schema)
6. [IPC Communication](#6-ipc-communication)
7. [DB State Synchronization](#7-db-state-synchronization)
8. [Implementation Details](#8-implementation-details)
9. [Edge Cases & Solutions](#9-edge-cases--solutions)
10. [Comparison with Daemon](#10-comparison-with-daemon)
11. [Implementation Roadmap](#11-implementation-roadmap)

---

## 1. The Architecture

### Core Concept

```
NO DAEMON - Each VM is its own persistent process:

┌─────────────────────────────────────────────────┐
│ Database (instances.db) - Source of Truth       │
├─────────┬────────┬──────────┬──────────┬────────────┤
│ vm_id   │ name   │ status   │ qemu_pid │runner_pid  │
├─────────┼────────┼──────────┼──────────┼────────────┤
│ vm1     │ MyVM   │ running  │ 12345    │ 12340      │ ← VM runner process PID
│ vm2     │ Server │ running  │ 23456    │ 23450      │ ← Different process
│ vm3     │ Test   │ stopped  │ NULL     │ NULL       │ ← No process
└─────────┴────────┴──────────┴──────────┴────────────┘

┌──────────────────────────────────────┐
│ VM Runner Process (vm1)              │  ← PID 12340
│ "python3 -m maqet.vm_runner vm1"     │
│                                      │
│  ├─ QEMUMachine(vm1) instance        │  ← Stays alive
│  │   ├─ QMP socket connection        │  ← File descriptor
│  │   └─ QEMU process (PID 12345)     │
│  │                                   │
│  ├─ IPC Server                       │
│  │   (Unix socket: vm1.sock)         │  ← CLI connects here
│  │                                   │
│  ├─ Event Loop:                      │
│  │   ├─ Handle IPC requests          │
│  │   ├─ Monitor QEMU process         │
│  │   ├─ Check DB for state drift     │
│  │   └─ Handle QMP events            │
│  │                                   │
│  └─ Exit when:                       │
│      - QEMU exits                    │
│      - DB says status=stopped        │
│      - Received stop command         │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ VM Runner Process (vm2)              │  ← PID 23450
│ "python3 -m maqet.vm_runner vm2"     │
│                                      │
│  ├─ QEMUMachine(vm2) instance        │  ← Independent
│  ├─ IPC Server (vm2.sock)            │
│  └─ Event Loop                       │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ CLI Process (ephemeral)              │
│ "maqet qmp vm1 query-status"         │
│                                      │
│  1. Read DB: vm1 has runner_pid=12340│
│  2. Check process alive              │
│  3. Connect: /run/.../vm1.sock       │
│  4. Send: {"method": "qmp", ...}     │
│  5. Receive response                 │
│  6. Exit                             │
└──────────────────────────────────────┘
```

**Key Properties**:

1. **One VM = One persistent Python process (VM Runner)**
2. **QEMUMachine instance lives in VM runner process**
3. **No central daemon** (no single point of failure)
4. **DB is source of truth** (runner_pid stored)
5. **Self-monitoring** (runner checks DB for drift)
6. **Independent lifecycle** (each VM runner is independent)

---

## 2. Why This Is Better

### Advantages Over Daemon Architecture

#### A. No Single Point of Failure

**Daemon approach**:

```
Daemon crashes → All VMs lose management → All QMP broken
```

**Per-VM approach**:

```
VM1 manager crashes → Only VM1 affected → VM2, VM3 unaffected
```

#### B. Simpler Lifecycle

**Daemon approach**:

```
Daemon must:
- Track all VMs in memory
- Handle VM crashes
- Recover state on daemon restart
- Manage VM registry
- Handle concurrent access
```

**Per-VM approach**:

```
VM runner must:
- Track one VM
- Exit when VM exits
- No recovery needed (process = VM)
- No registry (just one VM)
- No concurrency (one VM)
```

#### C. Natural Process Model

**Daemon approach**:

```
Daemon (PID 1000)
  ├─ Manages VM1 (QEMU PID 1001)
  ├─ Manages VM2 (QEMU PID 1002)
  └─ Manages VM3 (QEMU PID 1003)

Problem: Daemon lifecycle != VM lifecycle
```

**Per-VM approach**:

```
VM1 Runner (PID 1000)
  └─ QEMU VM1 (PID 1001)

VM2 Runner (PID 1002)
  └─ QEMU VM2 (PID 1003)

Solution: Runner lifecycle = VM lifecycle
```

#### D. DB as Source of Truth

**Daemon approach**:

```
State in daemon memory (_machines dict)
State in database (instances.db)
Problem: Two sources of truth, can diverge
```

**Per-VM approach**:

```
State ONLY in database (instances.db)
VM process existence = VM running
Problem solved: One source of truth
```

#### E. No Mixed-Mode Problem

**Daemon approach**:

```
VM started directly → Manager in CLI (QMP works)
VM started by daemon → Manager in daemon (QMP works)
VM started directly, daemon started → QMP routed to daemon (FAILS)
```

**Per-VM approach**:

```
VM always started by spawning VM runner process
No mixed modes possible
QMP always works
```

#### F. Easier Debugging

**Daemon approach**:

```
$ ps aux | grep maqet
user  1000  maqet-daemon (managing vm1, vm2, vm3???)

Problem: One process, hard to see what it's doing
```

**Per-VM approach**:

```
$ ps aux | grep maqet
user  1000  python3 -m maqet.vm_runner vm1
user  1002  python3 -m maqet.vm_runner vm2

Solution: One process per VM, clear what each does
```

#### G. Resource Isolation

Each VM runner process has:

- Own memory space
- Own file descriptors
- Own CPU scheduling
- Crashes don't affect other VMs

#### H. Simpler Concurrency

**Daemon approach**: Must handle concurrent CLI requests (locks, threads, queues)

**Per-VM approach**: Each VM runner is single-threaded, no concurrency issues

---

## 3. Component Design

### Component 1: VM Runner Process

**File**: `maqet/vm_runner.py`

**Purpose**: Persistent process that runs one VM's QEMUMachine instance.

```python
#!/usr/bin/env python3
"""VM Runner Process - runs one VM's QEMUMachine instance."""

import sys
import signal
import time
from pathlib import Path
from maqet.maqet import Maqet
from maqet.state import StateManager
from maqet.ipc.server import UnixSocketIPCServer

class VMRunner:
    """Runs a single VM's QEMUMachine instance."""

    def __init__(self, vm_id: str):
        self.vm_id = vm_id
        self.maqet = Maqet()  # Local Maqet instance
        self.machine = None  # QEMUMachine instance
        self.ipc_server = None
        self.running = True

        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

    def start(self):
        """Initialize VM runner, start VM, run event loop."""
        # 1. Load VM from database
        vm = self.maqet.state_manager.get_vm(self.vm_id)
        if not vm:
            print(f"VM {self.vm_id} not found in database", file=sys.stderr)
            sys.exit(1)

        # 2. Start QEMU via Maqet (creates QEMUMachine)
        try:
            self.maqet.start(self.vm_id, detach=False)  # Synchronous start
            self.machine = self.maqet._machines[self.vm_id]
        except Exception as e:
            print(f"Failed to start VM: {e}", file=sys.stderr)
            sys.exit(1)

        # 3. Update database with runner PID
        self.maqet.state_manager.update_vm(
            self.vm_id,
            runner_pid=os.getpid(),
            status="running"
        )

        # 4. Start IPC server
        socket_path = self._get_socket_path()
        self.ipc_server = UnixSocketIPCServer(
            socket_path=socket_path,
            handler=self._handle_ipc_request
        )
        self.ipc_server.start()

        # 5. Run event loop
        self._run_event_loop()

    def _run_event_loop(self):
        """Main event loop: monitor QEMU, handle IPC, check DB."""
        last_db_check = time.time()
        db_check_interval = 5  # Check DB every 5 seconds

        while self.running:
            # Check if QEMU process still running
            if not self._is_qemu_running():
                self._handle_qemu_exit()
                break

            # Handle IPC requests (non-blocking)
            self.ipc_server.process_requests(timeout=0.1)

            # Periodic DB state check (detect drift)
            if time.time() - last_db_check >= db_check_interval:
                if not self._check_db_consistency():
                    self._handle_db_stop_command()
                    break
                last_db_check = time.time()

            time.sleep(0.1)

        # Cleanup on exit
        self._cleanup()

    def _is_qemu_running(self) -> bool:
        """Check if QEMU process is still alive."""
        if not self.machine:
            return False

        # QEMUMachine has internal process tracking
        return self.machine._qemu_process.poll() is None

    def _check_db_consistency(self) -> bool:
        """Check if DB state matches reality (detect drift).

        Returns:
            True if consistent (continue running)
            False if DB says stop (should exit)
        """
        vm = self.maqet.state_manager.get_vm(self.vm_id)
        if not vm:
            # VM deleted from DB → stop
            return False

        if vm.status == "stopped":
            # DB says stopped but we're running → drift detected → stop
            return False

        if vm.runner_pid and vm.runner_pid != os.getpid():
            # DB has different runner PID → another runner started → stop
            return False

        return True

    def _handle_qemu_exit(self):
        """QEMU process exited, cleanup and exit manager."""
        print(f"QEMU for {self.vm_id} exited, cleaning up...")

        # Update database
        self.maqet.state_manager.update_vm(
            self.vm_id,
            status="stopped",
            qemu_pid=None,
            runner_pid=None,
            socket_path=None
        )

        self.running = False

    def _handle_db_stop_command(self):
        """DB says VM should be stopped (drift or manual stop)."""
        print(f"DB indicates {self.vm_id} should stop, shutting down...")

        # Stop QEMU gracefully
        if self.machine and self._is_qemu_running():
            try:
                self.machine.shutdown()
            except Exception as e:
                # Force kill if graceful shutdown fails
                self.machine._qemu_process.kill()

        self.running = False

    def _handle_ipc_request(self, request: dict) -> dict:
        """Handle IPC request from CLI.

        Args:
            request: {
                "method": "qmp",
                "args": ["query-status"],
                "kwargs": {}
            }

        Returns:
            {"status": "success", "result": ...} or {"status": "error", "error": ...}
        """
        method_name = request.get("method")
        args = request.get("args", [])
        kwargs = request.get("kwargs", {})

        try:
            # Special methods handled directly
            if method_name == "qmp":
                # QMP command: args = [command, **qmp_kwargs]
                result = self.machine.qmp(args[0], **kwargs)
                return {"status": "success", "result": result}

            elif method_name == "stop":
                # Stop VM
                self._handle_db_stop_command()
                return {"status": "success", "result": "VM stopping"}

            elif method_name == "status":
                # Get VM status
                status = {
                    "vm_id": self.vm_id,
                    "qemu_pid": self.machine.get_pid(),
                    "runner_pid": os.getpid(),
                    "running": self._is_qemu_running()
                }
                return {"status": "success", "result": status}

            else:
                return {"status": "error", "error": f"Unknown method: {method_name}"}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _handle_signal(self, signum, frame):
        """Handle termination signals."""
        print(f"Received signal {signum}, stopping...")
        self.running = False

    def _cleanup(self):
        """Cleanup resources before exit."""
        if self.ipc_server:
            self.ipc_server.stop()

        socket_path = self._get_socket_path()
        if socket_path.exists():
            socket_path.unlink()

    def _get_socket_path(self) -> Path:
        """Get Unix socket path for this VM."""
        runtime_dir = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
        socket_dir = runtime_dir / "maqet" / "sockets"
        socket_dir.mkdir(parents=True, exist_ok=True)
        return socket_dir / f"{self.vm_id}.sock"


def main():
    """Entry point for VM runner process."""
    if len(sys.argv) != 2:
        print("Usage: python3 -m maqet.vm_runner <vm_id>", file=sys.stderr)
        sys.exit(1)

    vm_id = sys.argv[1]
    runner = VMRunner(vm_id)

    try:
        runner.start()
    except Exception as e:
        print(f"VM runner error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**Key Features**:

- ✅ Runs one VM (simple, focused)
- ✅ Persistent process (stays alive while VM runs)
- ✅ IPC server (Unix socket per VM)
- ✅ Event loop (monitors QEMU, handles requests, checks DB)
- ✅ DB consistency check (detects drift every 5 seconds)
- ✅ Clean exit (QEMU exit, DB stop, signal)

---

### Component 2: CLI Process Spawner

**File**: `maqet/process_spawner.py`

**Purpose**: Spawn VM runner process in detached mode.

```python
"""Process spawner for VM runner instances."""

import os
import sys
import subprocess
from pathlib import Path

def spawn_vm_runner(vm_id: str) -> int:
    """Spawn VM runner process in detached mode.

    Args:
        vm_id: VM identifier

    Returns:
        Runner process PID
    """
    # Get Python interpreter path
    python_exe = sys.executable

    # Build command
    cmd = [python_exe, "-m", "maqet.vm_runner", vm_id]

    # Spawn detached process (won't die when CLI exits)
    process = subprocess.Popen(
        cmd,
        start_new_session=True,  # Detach from parent process group
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Wait briefly to ensure process started
    time.sleep(0.5)

    # Check if process still alive (didn't crash immediately)
    if process.poll() is not None:
        # Process exited immediately → error
        stderr = process.stderr.read().decode()
        raise MaqetError(f"VM runner failed to start: {stderr}")

    return process.pid


def wait_for_vm_ready(vm_id: str, timeout: float = 10.0) -> bool:
    """Wait for VM runner to be ready (IPC socket exists).

    Args:
        vm_id: VM identifier
        timeout: Maximum wait time in seconds

    Returns:
        True if ready, False if timeout
    """
    socket_path = _get_socket_path(vm_id)
    start_time = time.time()

    while time.time() - start_time < timeout:
        if socket_path.exists():
            # Try to connect to verify it's working
            try:
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.connect(str(socket_path))
                sock.close()
                return True
            except:
                pass

        time.sleep(0.1)

    return False


def _get_socket_path(vm_id: str) -> Path:
    """Get Unix socket path for VM."""
    runtime_dir = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
    return runtime_dir / "maqet" / "sockets" / f"{vm_id}.sock"
```

---

### Component 3: CLI to VM Runner Client

**File**: `maqet/ipc/runner_client.py`

**Purpose**: CLI communicates with VM runner process.

```python
"""Client for communicating with VM runner processes."""

import socket
import json
import os
import psutil
from pathlib import Path

class RunnerClient:
    """Client for communicating with a VM runner process."""

    def __init__(self, vm_id: str, state_manager):
        self.vm_id = vm_id
        self.state_manager = state_manager
        self.socket_path = self._get_socket_path()

    def is_runner_running(self) -> bool:
        """Check if VM runner process is running."""
        vm = self.state_manager.get_vm(self.vm_id)
        if not vm or not vm.runner_pid:
            return False

        # Check if process exists and is alive
        return psutil.pid_exists(vm.runner_pid)

    def send_request(self, method: str, *args, **kwargs) -> dict:
        """Send IPC request to VM runner.

        Args:
            method: Method name (e.g., "qmp", "stop", "status")
            *args: Method arguments
            **kwargs: Method keyword arguments

        Returns:
            Result dict from manager

        Raises:
            MaqetError: If runner not running or communication fails
        """
        # Check runner running
        if not self.is_runner_running():
            raise MaqetError(f"VM runner for {self.vm_id} is not running")

        # Check socket exists
        if not self.socket_path.exists():
            raise MaqetError(f"Socket not found: {self.socket_path}")

        # Connect to Unix socket
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.connect(str(self.socket_path))

            # Send request
            request = {
                "method": method,
                "args": list(args),
                "kwargs": kwargs
            }
            sock.sendall(json.dumps(request).encode() + b"\n")

            # Receive response
            response_data = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response_data += chunk
                if b"\n" in chunk:  # End of message
                    break

            response = json.loads(response_data.decode())

            # Check response status
            if response["status"] == "error":
                raise MaqetError(response["error"])

            return response["result"]

        except socket.error as e:
            raise MaqetError(f"Communication error: {e}")
        finally:
            sock.close()

    def _get_socket_path(self) -> Path:
        """Get Unix socket path for this VM."""
        runtime_dir = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
        return runtime_dir / "maqet" / "sockets" / f"{self.vm_id}.sock"
```

---

## 4. Process Lifecycle

### Lifecycle 1: Start VM

```
┌──────────────────────────────────────────┐
│ User: maqet start vm1                    │
└────────────┬─────────────────────────────┘
             │
             ↓
┌────────────────────────────────────────────────────┐
│ CLI Process (Maqet.start)                          │
│                                                    │
│ 1. Load config from DB                             │
│ 2. Validate config                                 │
│ 3. Create VM entry in DB (status=starting)         │
│ 4. Spawn VM runner process:                       │
│    subprocess.Popen(                               │
│        ["python3", "-m", "maqet.vm_runner", "vm1"], │
│        start_new_session=True,  # Detach           │
│        stdin=DEVNULL,                              │
│        stdout=PIPE,                                │
│        stderr=PIPE                                 │
│    )                                               │
│ 5. Wait for socket: /run/.../vm1.sock              │
│ 6. Return success to user                          │
│ 7. CLI exits                                       │
└────────────┬───────────────────────────────────────┘
             │
             ↓ (VM runner process continues)
┌─────────────────────────────────────────────────────┐
│ VM Runner Process (PID 12340)                      │
│ "python3 -m maqet.vm_runner vm1"                    │
│                                                     │
│ 1. Load VM from DB                                  │
│ 2. Create Maqet() instance                          │
│ 3. Start QEMU:                                      │
│    - machine = QEMUMachine(binary, args)            │
│    - machine.launch()                               │
│    - Store in self.maqet._machines["vm1"]           │
│ 4. Update DB:                                       │
│    - status=running                                 │
│    - qemu_pid=12345                                 │
│    - runner_pid=12340 (self PID)                   │
│    - socket_path=/run/.../vm1.sock                  │
│ 5. Start IPC server (Unix socket)                   │
│ 6. Enter event loop (stays alive):                  │
│    while running:                                   │
│        - Check QEMU alive                           │
│        - Handle IPC requests                        │
│        - Check DB for drift (every 5s)              │
│        - Sleep 0.1s                                 │
└─────────────────────────────────────────────────────┘
```

**Result**:

- VM is running (QEMU PID 12345)
- VM runner is running (PID 12340)
- DB has both PIDs
- Unix socket available for CLI communication

---

### Lifecycle 2: QMP Command

```
┌──────────────────────────────────────────┐
│ User: maqet qmp vm1 query-status         │
└────────────┬─────────────────────────────┘
             │
             ↓
┌──────────────────────────────────────────────────────┐
│ CLI Process (Maqet.qmp)                              │
│                                                      │
│ 1. Read DB: get VM vm1                               │
│    - runner_pid=12340                               │
│    - socket_path=/run/.../vm1.sock                   │
│                                                      │
│ 2. Check runner alive:                               │
│    if not psutil.pid_exists(12340):                  │
│        raise MaqetError("VM runner not running")     │
│                                                      │
│ 3. Connect to Unix socket:                           │
│    sock.connect("/run/.../vm1.sock")                 │
│                                                      │
│ 4. Send IPC request:                                 │
│    {                                                 │
│        "method": "qmp",                              │
│        "args": ["query-status"],                     │
│        "kwargs": {}                                  │
│    }                                                 │
│                                                      │
│ 5. Receive response:                                 │
│    {                                                 │
│        "status": "success",                          │
│        "result": {"running": true, "status": "running"}│
│    }                                                 │
│                                                      │
│ 6. Display result to user                            │
│ 7. CLI exits                                         │
└────────────┬─────────────────────────────────────────┘
             │ IPC Request
             ↓
┌─────────────────────────────────────────────────────┐
│ VM Runner Process (PID 12340)                      │
│                                                     │
│ Event Loop:                                         │
│   - IPC server receives request                     │
│   - Parse: method=qmp, args=["query-status"]        │
│   - Execute: self.machine.qmp("query-status")       │
│   - QMP socket communication (already connected)    │
│   - Get result: {"running": true, ...}              │
│   - Send response: {"status": "success", ...}       │
│   - Continue event loop                             │
└─────────────────────────────────────────────────────┘
```

**Key Point**: QEMUMachine instance and QMP socket never leave the VM runner process. No file descriptor transfer needed.

---

### Lifecycle 3: Stop VM

```
┌──────────────────────────────────────────┐
│ User: maqet stop vm1                     │
└────────────┬─────────────────────────────┘
             │
             ↓
┌──────────────────────────────────────────────────────┐
│ CLI Process (Maqet.stop)                             │
│                                                      │
│ Option A: Send stop via IPC                          │
│ 1. Connect to VM runner                             │
│ 2. Send: {"method": "stop"}                          │
│ 3. Wait for response                                 │
│ 4. CLI exits                                         │
│                                                      │
│ Option B: Update DB, let runner detect               │
│ 1. Update DB: status=stopped                         │
│ 2. VM runner detects in next DB check (5s)           │
│ 3. CLI exits                                         │
└────────────┬─────────────────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────────────────┐
│ VM Runner Process (PID 12340)                      │
│                                                     │
│ Option A: Received stop command via IPC              │
│   - Call machine.shutdown() (graceful QMP quit)     │
│   - Wait for QEMU to exit                           │
│   - Update DB: status=stopped, pids=NULL            │
│   - Stop IPC server                                 │
│   - Remove socket file                              │
│   - Exit process (code 0)                           │
│                                                     │
│ Option B: Detected DB status=stopped                │
│   - DB check sees vm.status == "stopped"            │
│   - Call machine.shutdown()                         │
│   - Same cleanup as above                           │
└─────────────────────────────────────────────────────┘
```

**Result**:

- QEMU stopped (PID 12345 gone)
- VM runner stopped (PID 12340 gone)
- DB updated: status=stopped, pids=NULL
- Socket removed

---

### Lifecycle 4: QEMU Crashes

```
┌─────────────────────────────────────────────────────┐
│ VM Runner Process (PID 12340)                      │
│ Event Loop running...                               │
│                                                     │
│ Iteration N:                                        │
│   - Check QEMU alive:                               │
│     if machine._qemu_process.poll() is None:  ← QEMU exited!
│         continue                                    │
│     else:                                           │
│         _handle_qemu_exit()                         │
│                                                     │
│ _handle_qemu_exit():                                │
│   1. Detect: QEMU process no longer running         │
│   2. Update DB:                                     │
│      - status=stopped                               │
│      - qemu_pid=NULL                                │
│      - runner_pid=NULL                             │
│   3. Log: "QEMU exited (crash or shutdown)"         │
│   4. Stop IPC server                                │
│   5. Remove socket                                  │
│   6. Exit runner process                             │
└─────────────────────────────────────────────────────┘
```

**Result**:

- QEMU crash detected immediately (poll returns exit code)
- VM runner cleans up and exits
- DB reflects stopped state
- No orphaned processes

---

### Lifecycle 5: DB Drift Detection

```
Scenario: User manually updates DB (or DB corruption)

Database state:
├─ vm_id=vm1, status=stopped  ← Manually changed
├─ runner_pid=NULL
└─ qemu_pid=NULL

Reality:
├─ VM Runner running (PID 12340)
└─ QEMU running (PID 12345)

┌─────────────────────────────────────────────────────┐
│ VM Runner Process (PID 12340)                      │
│ Event Loop running...                               │
│                                                     │
│ Iteration N (5 seconds since last DB check):        │
│   - _check_db_consistency():                        │
│     vm = state_manager.get_vm("vm1")                │
│     if vm.status == "stopped":  ← Drift detected!   │
│         return False  # Inconsistent                │
│                                                     │
│   - _handle_db_stop_command():                      │
│     1. Log: "DB says stop, shutting down"           │
│     2. Call machine.shutdown() (graceful)           │
│     3. Update DB (already stopped)                  │
│     4. Exit runner                                   │
└─────────────────────────────────────────────────────┘
```

**Result**:

- Drift detected within 5 seconds
- VM runner self-corrects (stops QEMU)
- DB becomes consistent
- No manual intervention needed

---

## 5. Database Schema

### Updated Schema

```sql
CREATE TABLE vm_instances (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    config_data TEXT NOT NULL,      -- JSON config
    status TEXT NOT NULL,            -- "running", "stopped", "starting", "stopping"
    qemu_pid INTEGER,                -- QEMU process PID (NULL if stopped)
    runner_pid INTEGER,             -- VM runner process PID (NULL if stopped)
    socket_path TEXT,                -- Unix socket path (NULL if stopped)
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX idx_status ON vm_instances(status);
CREATE INDEX idx_runner_pid ON vm_instances(runner_pid);
```

**New Fields**:

- `runner_pid`: VM runner process PID (enables CLI to find process)
- `socket_path`: Unix socket path (enables CLI to connect)

**Field Relationships**:

```
status=running  → qemu_pid != NULL, runner_pid != NULL, socket_path != NULL
status=stopped  → qemu_pid = NULL, runner_pid = NULL, socket_path = NULL
status=starting → qemu_pid = NULL, runner_pid = NULL (transitional)
status=stopping → qemu_pid != NULL, runner_pid != NULL (transitional)
```

---

## 6. IPC Communication

### IPC Protocol: JSON-RPC over Unix Socket

**Why Unix socket?**

- ✅ Lowest latency for local IPC
- ✅ Filesystem permissions (security)
- ✅ No port conflicts
- ✅ Simple implementation (no dependencies)
- ✅ Each VM has own socket (no routing needed)

**Socket Naming**:

```
/run/user/{uid}/maqet/sockets/{vm_id}.sock

Examples:
/run/user/1000/maqet/sockets/vm1.sock
/run/user/1000/maqet/sockets/server-vm.sock
/run/user/1000/maqet/sockets/test-debian.sock
```

**Message Format**:

Request:

```json
{
    "method": "qmp",
    "args": ["query-status"],
    "kwargs": {}
}
```

Response (success):

```json
{
    "status": "success",
    "result": {
        "running": true,
        "status": "running"
    }
}
```

Response (error):

```json
{
    "status": "error",
    "error": "VM not found"
}
```

**Supported Methods**:

- `qmp`: Execute QMP command (args=[command, **qmp_kwargs])
- `stop`: Stop VM gracefully
- `status`: Get VM runtime status
- `ping`: Health check (returns "pong")

---

## 7. DB State Synchronization

### Synchronization Strategy

**Problem**: DB and reality can diverge if:

1. VM runner crashes (QEMU still running)
2. Manual DB manipulation
3. QEMU crashes (DB not updated)
4. Process killed (SIGKILL, no cleanup)

**Solution**: Periodic consistency checks in both directions.

#### Direction 1: VM Runner → DB (Every 5 seconds)

```python
def _check_db_consistency(self) -> bool:
    """Check if DB state matches our state."""
    vm = self.state_manager.get_vm(self.vm_id)

    # Check 1: VM deleted from DB
    if not vm:
        LOG.warning("VM deleted from DB, stopping")
        return False  # Exit

    # Check 2: DB says stopped
    if vm.status == "stopped":
        LOG.warning("DB says stopped, stopping")
        return False  # Exit

    # Check 3: DB has different runner PID
    if vm.runner_pid and vm.runner_pid != os.getpid():
        LOG.warning("DB has different runner PID, stopping")
        return False  # Exit (another manager started)

    # Check 4: QEMU PID mismatch
    if vm.qemu_pid != self.machine.get_pid():
        LOG.warning("QEMU PID mismatch, updating DB")
        self.state_manager.update_vm(
            self.vm_id,
            qemu_pid=self.machine.get_pid()
        )

    return True  # All consistent
```

#### Direction 2: CLI → DB (Before every command)

```python
def _cleanup_dead_processes(self):
    """Check all VMs, clean up dead runner processes."""
    for vm in self.state_manager.list_vms():
        if vm.status == "running" and vm.runner_pid:
            # Check if runner process alive
            if not psutil.pid_exists(vm.runner_pid):
                LOG.warning(f"VM {vm.id} runner dead, marking stopped")
                self.state_manager.update_vm(
                    vm.id,
                    status="stopped",
                    qemu_pid=None,
                    runner_pid=None,
                    socket_path=None
                )

            # Check if QEMU process alive
            elif vm.qemu_pid and not psutil.pid_exists(vm.qemu_pid):
                LOG.warning(f"VM {vm.id} QEMU dead, marking stopped")
                self.state_manager.update_vm(
                    vm.id,
                    status="stopped",
                    qemu_pid=None,
                    runner_pid=None,
                    socket_path=None
                )
                # Kill orphaned runner process
                try:
                    os.kill(vm.runner_pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
```

**When to run**: On Maqet initialization (`__init__`).

---

## 8. Implementation Details

### Updated Maqet.start()

```python
def start(self, vm_id: str, detach: bool = True):
    """Start a VM by spawning VM runner process.

    Args:
        vm_id: VM identifier
        detach: If True, spawn runner and return immediately.
                If False, start VM in foreground (for testing).
    """
    # 1. Load and validate config
    vm = self.state_manager.get_vm(vm_id)
    if not vm:
        raise MaqetError(f"VM {vm_id} not found")

    if vm.status == "running":
        raise MaqetError(f"VM {vm_id} already running")

    # 2. Update DB: status=starting
    self.state_manager.update_vm(vm_id, status="starting")

    # 3. Spawn VM runner process
    from maqet.process_spawner import spawn_vm_runner, wait_for_vm_ready

    try:
        runner_pid = spawn_vm_runner(vm_id)

        # Wait for VM to be ready (socket available)
        if not wait_for_vm_ready(vm_id, timeout=30):
            raise MaqetError("VM failed to start (timeout)")

        LOG.info(f"VM {vm_id} started (runner PID {runner_pid})")
        return {"vm_id": vm_id, "runner_pid": runner_pid}

    except Exception as e:
        # Cleanup on failure
        self.state_manager.update_vm(vm_id, status="stopped")
        raise MaqetError(f"Failed to start VM: {e}")
```

### Updated Maqet.qmp()

```python
def qmp(self, vm_id: str, command: str, **kwargs):
    """Execute QMP command on VM.

    Args:
        vm_id: VM identifier
        command: QMP command name
        **kwargs: QMP command arguments
    """
    # Get VM from DB
    vm = self.state_manager.get_vm(vm_id)
    if not vm:
        raise MaqetError(f"VM {vm_id} not found")

    if vm.status != "running":
        raise MaqetError(f"VM {vm_id} is not running")

    # Connect to VM runner via IPC
    from maqet.ipc.vm_client import VMClient

    client = VMClient(vm_id, self.state_manager)
    result = client.send_request("qmp", command, **kwargs)

    return result
```

### Updated Maqet.stop()

```python
def stop(self, vm_id: str, force: bool = False):
    """Stop a VM.

    Args:
        vm_id: VM identifier
        force: If True, kill immediately. If False, graceful shutdown.
    """
    vm = self.state_manager.get_vm(vm_id)
    if not vm:
        raise MaqetError(f"VM {vm_id} not found")

    if vm.status != "running":
        raise MaqetError(f"VM {vm_id} is not running")

    if force:
        # Kill runner process (will cleanup)
        if vm.runner_pid and psutil.pid_exists(vm.runner_pid):
            os.kill(vm.runner_pid, signal.SIGKILL)

        # Update DB immediately
        self.state_manager.update_vm(
            vm_id,
            status="stopped",
            qemu_pid=None,
            runner_pid=None,
            socket_path=None
        )
    else:
        # Send stop command via IPC (graceful)
        from maqet.ipc.vm_client import VMClient

        client = VMClient(vm_id, self.state_manager)
        client.send_request("stop")

        # Wait for runner to exit
        timeout = 30
        start = time.time()
        while time.time() - start < timeout:
            if not psutil.pid_exists(vm.runner_pid):
                break
            time.sleep(0.5)

    LOG.info(f"VM {vm_id} stopped")
```

---

## 9. Edge Cases & Solutions

### Edge Case 1: VM Runner Crashes

**Problem**: VM runner crashes, QEMU still running, DB says running.

**Detection**:

- CLI runs `_cleanup_dead_processes()` on startup
- Checks `psutil.pid_exists(vm.runner_pid)`
- Finds runner dead

**Solution**:

```python
# Update DB
self.state_manager.update_vm(
    vm_id,
    status="stopped",  # Mark as stopped (no runner)
    runner_pid=None,
    socket_path=None
    # Keep qemu_pid for forensics
)

# Optionally: Kill orphaned QEMU process
if vm.qemu_pid and psutil.pid_exists(vm.qemu_pid):
    LOG.warning(f"Killing orphaned QEMU process {vm.qemu_pid}")
    os.kill(vm.qemu_pid, signal.SIGTERM)
```

---

### Edge Case 2: QEMU Crashes

**Problem**: QEMU crashes, runner still running.

**Detection**: VM runner event loop checks `machine._qemu_process.poll()`.

**Solution**: Runner calls `_handle_qemu_exit()`, updates DB, exits.

---

### Edge Case 3: Multiple Runners for Same VM

**Problem**: User starts VM twice quickly, two runners spawn.

**Prevention**:

```python
# In Maqet.start(), before spawning:
vm = self.state_manager.get_vm(vm_id)
if vm.status == "running":
    # Already running, don't spawn
    raise MaqetError(f"VM {vm_id} already running")

# Atomic DB update (status=starting)
self.state_manager.update_vm(vm_id, status="starting")
```

**Detection (in VM runner)**:

```python
# Before starting QEMU, check DB again
vm = self.state_manager.get_vm(vm_id)
if vm.runner_pid and vm.runner_pid != os.getpid():
    # Another runner already running
    LOG.error("Another runner running, exiting")
    sys.exit(1)

# Update DB with our PID atomically
self.state_manager.update_vm(vm_id, runner_pid=os.getpid())
```

---

### Edge Case 4: Socket File Conflicts

**Problem**: Socket file exists from crashed runner.

**Solution**:

```python
# In VM runner, before creating socket:
socket_path = self._get_socket_path()
if socket_path.exists():
    # Try to connect (check if someone using it)
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(str(socket_path))
        sock.close()
        # Someone is using it → error
        raise MaqetError(f"Socket already in use: {socket_path}")
    except socket.error:
        # No one listening → stale socket, remove it
        socket_path.unlink()

# Now create socket
self.ipc_server.bind(socket_path)
```

---

### Edge Case 5: DB Locked (SQLite Concurrency)

**Problem**: Multiple processes (manager + CLI) access DB simultaneously, SQLite locks.

**Solution**:

```python
# Use WAL mode (Write-Ahead Logging) for better concurrency
connection.execute("PRAGMA journal_mode=WAL")

# Set busy timeout (wait up to 5s for lock)
connection.execute("PRAGMA busy_timeout=5000")

# Retry on lock errors
for attempt in range(3):
    try:
        cursor.execute(query, params)
        connection.commit()
        break
    except sqlite3.OperationalError as e:
        if "locked" in str(e) and attempt < 2:
            time.sleep(0.1 * (attempt + 1))
        else:
            raise
```

---

### Edge Case 6: User Deletes VM While Running

**Problem**: `maqet rm vm1` while VM is running.

**Current Behavior**:

```python
# Maqet.rm() should check status
def rm(self, vm_id: str, force: bool = False):
    vm = self.state_manager.get_vm(vm_id)
    if vm.status == "running" and not force:
        raise MaqetError("VM is running, use --force to stop and remove")

    if force and vm.status == "running":
        # Stop first
        self.stop(vm_id, force=True)

    # Remove from DB
    self.state_manager.delete_vm(vm_id)
```

**What happens to manager?**

- Manager detects VM deleted in next DB check (5s)
- `_check_db_consistency()` returns False
- Manager stops QEMU and exits

---

## 10. Comparison with Daemon

### Feature Comparison

| Feature | Daemon Architecture | Per-VM Process | Winner |
|---------|---------------------|----------------|--------|
| Single point of failure | Yes (daemon) | No (each VM independent) | Per-VM ✅ |
| Process model | Complex (daemon manages all) | Simple (1 VM = 1 process) | Per-VM ✅ |
| Lifecycle coupling | Daemon ≠ VM | Manager = VM | Per-VM ✅ |
| Resource isolation | Shared daemon | Per-VM isolation | Per-VM ✅ |
| Debugging | Hard (all VMs in one process) | Easy (ps shows each VM) | Per-VM ✅ |
| Concurrency issues | Yes (locks, threads) | No (one VM per process) | Per-VM ✅ |
| State recovery | Complex (daemon restart) | Simple (no recovery needed) | Per-VM ✅ |
| DB as source of truth | No (memory + DB) | Yes (only DB) | Per-VM ✅ |
| Mixed-mode problem | Yes | No | Per-VM ✅ |
| IPC complexity | Central routing | Direct (socket per VM) | Per-VM ✅ |
| Daemon management | User must manage | No daemon | Per-VM ✅ |
| Implementation complexity | High | Medium | Per-VM ✅ |

**Winner: Per-VM Process Architecture** (11/12 categories)

---

### Code Complexity Comparison

**Daemon Architecture**:

- `maqet/manager_daemon.py` (~400 lines) - Daemon lifecycle, event loop
- `maqet/ipc/server.py` (~200 lines) - IPC server with routing
- `maqet/ipc/client.py` (~200 lines) - Client with auto-start
- `maqet/process_spawner.py` (~150 lines) - Daemonization (fork/systemd)
- State recovery logic (~100 lines)
- Concurrency handling (~50 lines)
- **Total: ~1,100 lines**

**Per-VM Architecture**:

- `maqet/vm_runner.py` (~300 lines) - VM runner process
- `maqet/ipc/unix_socket_server.py` (~100 lines) - Simple socket server
- `maqet/ipc/vm_client.py` (~100 lines) - Simple client
- `maqet/process_spawner.py` (~80 lines) - Just spawn, no daemonization
- DB consistency checks (~50 lines)
- **Total: ~630 lines**

**Savings: ~470 lines (43% less code)**

---

## 11. Implementation Roadmap

### Phase 1: Core VM Manager (Week 1)

**Tasks**:

1. Create `maqet/vm_manager.py`:
   - `VMManager` class
   - Event loop (QEMU monitoring, IPC, DB checks)
   - Signal handlers
   - Socket cleanup

2. Create `maqet/ipc/unix_socket_server.py`:
   - Simple Unix socket server
   - JSON message protocol
   - Non-blocking request handling

3. Create `maqet/process_spawner.py`:
   - `spawn_vm_runner()` - detached process spawning
   - `wait_for_vm_ready()` - wait for socket

**Deliverable**: VM runner can run standalone, handle QEMU lifecycle.

**Testing**:

```bash
# Manual test
python3 -m maqet.vm_runner test-vm
# Should start QEMU, create socket, enter event loop
```

---

### Phase 2: Database Schema Update (Week 1)

**Tasks**:

1. Add `runner_pid` column to `vm_instances` table
2. Add `socket_path` column
3. Migration script for existing databases
4. Update `StateManager` CRUD operations

**Deliverable**: Database supports new fields.

---

### Phase 3: CLI Integration (Week 2)

**Tasks**:

1. Update `Maqet.start()`:
   - Spawn VM runner instead of direct start
   - Wait for socket
   - Return runner PID

2. Create `maqet/ipc/vm_client.py`:
   - `VMClient` class
   - Socket communication
   - Error handling

3. Update `Maqet.qmp()`:
   - Use `VMClient` to send commands
   - Remove `_machines` dict lookup

4. Update `Maqet.stop()`:
   - Send stop via IPC or kill process

**Deliverable**: All CLI commands work through VM runners.

---

### Phase 4: DB Consistency Checks (Week 2-3)

**Tasks**:

1. Implement `_cleanup_dead_processes()` in `Maqet.__init__`
2. Implement `_check_db_consistency()` in `VMRunner`
3. Add periodic DB check to VM runner event loop (every 5s)
4. Handle drift cases (DB says stop, runner running)

**Deliverable**: System self-heals from inconsistent states.

---

### Phase 5: Edge Case Handling (Week 3)

**Tasks**:

1. Handle VM runner crashes (orphaned QEMU)
2. Handle QEMU crashes (clean manager exit)
3. Handle socket conflicts (stale sockets)
4. Handle concurrent starts (prevent duplicate runners)
5. Handle DB locking (SQLite WAL mode, retries)

**Deliverable**: Robust error handling for all edge cases.

---

### Phase 6: Testing (Week 4)

**Tasks**:

1. Unit tests:
   - VM runner lifecycle
   - IPC communication
   - DB consistency checks
   - Process spawning

2. Integration tests:
   - Start/stop workflows
   - QMP commands via IPC
   - Crash recovery
   - Multi-VM scenarios

3. Stress tests:
   - Start 10 VMs simultaneously
   - Rapid start/stop cycles
   - Kill managers randomly (chaos testing)

**Deliverable**: Comprehensive test coverage (>80%).

---

### Phase 7: Migration & Documentation (Week 4-5)

**Tasks**:

1. Migration guide for existing users
2. Architecture documentation (this file)
3. Update CLAUDE.md with new architecture
4. Update README.md
5. Deprecation notices (if applicable)

**Deliverable**: Production-ready with full documentation.

---

## Conclusion

### Summary

**Can this be achieved?** **YES**, and it's **BETTER** than daemon architecture.

**Key advantages**:

1. ✅ No daemon (no explicit management)
2. ✅ No single point of failure (each VM independent)
3. ✅ Simple lifecycle (VM runner = VM lifetime)
4. ✅ DB is source of truth (one state location)
5. ✅ Self-healing (DB consistency checks)
6. ✅ Natural process model (one VM = one process)
7. ✅ Easy debugging (ps shows each VM)
8. ✅ Less code (~630 lines vs ~1,100)

**How it works**:

- Each VM runs in persistent Python process (`maqet.vm_runner`)
- QEMUMachine instance stays alive in that process
- CLI finds VM runner via PID in database
- CLI communicates via Unix socket (one per VM)
- VM runner monitors QEMU and DB (self-correcting)
- When QEMU exits, runner exits (natural cleanup)

**Why it works**:

- No central daemon bottleneck
- No state synchronization (DB is single truth)
- No mixed-mode confusion (always same path)
- No recovery needed (processes are VMs)

**Implementation**: 5 weeks for production-ready system.

This architecture is elegant, robust, and aligns perfectly with your insight: **"Why do we need a manager process in the background? Why can't every instance of VM by itself be an instance?"**

Answer: **It can, and it should.**
