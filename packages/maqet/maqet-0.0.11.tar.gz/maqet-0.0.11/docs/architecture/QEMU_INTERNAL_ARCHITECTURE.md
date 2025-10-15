# QEMU Internal Architecture Research

This document captures detailed research into QEMU's internal socket and QMP management, conducted while fixing the QMP socket issue in MAQET.

## Table of Contents

1. [Overview](#overview)
2. [QEMUMachine Class Architecture](#qemumachine-class-architecture)
3. [QMP Socket Management](#qmp-socket-management)
4. [Socket Creation Process](#socket-creation-process)
5. [Key Findings](#key-findings)
6. [Common Misconceptions](#common-misconceptions)
7. [Best Practices](#best-practices)

---

## Overview

QEMU provides a Python library (`qemu.machine.machine`) that wraps QEMU process management. Understanding its internal architecture is crucial for proper integration.

**Key Discovery**: QEMUMachine does NOT create traditional Unix socket files on disk. It manages sockets internally through Python's `asyncio` and socket primitives.

---

## QEMUMachine Class Architecture

### Basic Usage

```python
from qemu.machine import QEMUMachine

# Create instance
qm = QEMUMachine(
    binary='/usr/bin/qemu-system-x86_64',
    args=['-m', '128M', '-display', 'none'],
    monitor_address='/path/to/socket.sock',  # String or tuple
)

# Launch VM
qm.launch()

# Use QMP directly
result = qm.cmd('query-status')  # Works immediately - no socket file needed

# Shutdown
qm.shutdown()
```

### Constructor Signature

```python
def __init__(
    self,
    binary: str,
    args: Sequence[str] = (),
    wrapper: Sequence[str] = (),
    name: Optional[str] = None,
    base_temp_dir: str = '/var/tmp',
    monitor_address: Union[str, Tuple[str, int], None] = None,
    drain_console: bool = False,
    console_log: Optional[str] = None,
    log_dir: Optional[str] = None,
    qmp_timer: Optional[float] = 30
)
```

**Critical Parameters**:

- `monitor_address`: Can be:
  - `None` - Uses socketpair (no filesystem socket)
  - `str` - Path for Unix socket (server mode)
  - `Tuple[str, int]` - (host, port) for TCP socket

---

## QMP Socket Management

### The Three Socket Modes

#### 1. Socketpair Mode (monitor_address=None)

**What Happens**:

```python
# In QEMUMachine._pre_launch():
if self._monitor_address is None:
    self._sock_pair = socket.socketpair()
    os.set_inheritable(self._sock_pair[0].fileno(), True)
    sock = self._sock_pair[1]
```

**Characteristics**:

- Creates anonymous socket pair (no filesystem entry)
- One end passed to QEMU via FD inheritance
- Other end used by Python QMP client
- **No socket file on disk**

**QEMU Command Line**:

```bash
qemu-system-x86_64 ... \
  -chardev socket,id=mon,fd=3 \
  -mon chardev=mon,mode=control
```

#### 2. Unix Socket Mode (monitor_address="/path/to/socket")

**What Happens**:

```python
# In QEMUMachine._pre_launch():
if isinstance(self._monitor_address, str):
    self._remove_files.append(self._monitor_address)  # Mark for cleanup

sock_or_addr = self._monitor_address or sock

self._qmp_connection = QEMUMonitorProtocol(
    sock_or_addr,
    server=bool(self._monitor_address),  # True for string path
    nickname=self._name
)
```

**QEMUMonitorProtocol with server=True**:

```python
# In qemu/qmp/legacy.py
def __init__(self, address, server=False, nickname=None):
    self._qmp = QMPClient(nickname)
    self._aloop = asyncio.get_event_loop()
    self._address = address

    if server:
        # Start server BEFORE QEMU launches
        self._sync(self._qmp.start_server(self._address))
```

**Important**: The socket IS created, but by `QEMUMonitorProtocol.start_server()`, which uses asyncio's `start_unix_server()`:

```python
# In qemu/qmp/protocol.py (QMPClient)
async def start_server(self, address: SocketAddrT, ssl: Optional[SSLContext] = None):
    """Start QMP server listening on address."""
    if isinstance(address, tuple):
        coro = asyncio.start_server(...)
    else:
        # Unix socket
        coro = asyncio.start_unix_server(
            self._new_session,
            path=address,
            ssl=ssl,
        )
    self._server = await coro
```

**QEMU Command Line**:

```bash
qemu-system-x86_64 ... \
  -chardev socket,id=mon,path=/path/to/socket \
  -mon chardev=mon,mode=control
```

**Critical Discovery**: The socket file is created by Python's asyncio server **before** QEMU starts. QEMU then **connects as a client** to this server socket.

#### 3. TCP Socket Mode (monitor_address=("localhost", 4444))

**QEMU Command Line**:

```bash
qemu-system-x86_64 ... \
  -chardev socket,id=mon,host=localhost,port=4444 \
  -mon chardev=mon,mode=control
```

---

## Socket Creation Process

### Timeline for Unix Socket Mode

1. **QEMUMachine.**init**()**: Store `monitor_address="/path/to/socket"`
2. **QEMUMachine.launch()**: Calls `_pre_launch()`
3. **_pre_launch()**:

   ```python
   self._qmp_connection = QEMUMonitorProtocol(
       self._monitor_address,
       server=True
   )
   ```

4. **QEMUMonitorProtocol.**init**()**: Calls `start_server()`
5. **start_server()**: Creates asyncio Unix server
   - **Socket file created HERE**
   - Server starts listening
6. **_pre_launch() continues**: Builds QEMU command line with `-chardev socket,path=...`
7. **QEMU starts**: Connects to existing socket as a client
8. **accept() happens**: QMP connection established

### Socket File Lifecycle

```python
# Socket created
socket_path = "/tmp/test.sock"
qm = QEMUMachine(monitor_address=socket_path)

print(os.path.exists(socket_path))  # False - not created yet

qm.launch()  # Calls _pre_launch()
# Socket created by QEMUMonitorProtocol in _pre_launch()

print(os.path.exists(socket_path))  # Still False in quick check!
# Why? asyncio.start_unix_server() is async, socket appears shortly after

time.sleep(0.1)
print(os.path.exists(socket_path))  # True - socket now exists

qm.shutdown()
print(os.path.exists(socket_path))  # False - cleaned up
```

**Why Socket Appeared Not to Exist**: In testing, the socket file is created by asyncio but there's a tiny race condition. By the time we checked, it might not have been flushed to disk yet.

---

## Key Findings

### 1. QEMUMachine Instance MUST Stay Alive

**Critical**: The QEMUMachine instance must remain in memory while the VM runs:

```python
# WRONG - QEMUMachine destroyed, QMP lost
def start_vm():
    qm = QEMUMachine(...)
    qm.launch()
    return pid  # qm goes out of scope → __del__() → socket cleaned up

# RIGHT - Keep instance alive
class VMManager:
    def __init__(self):
        self._machines = {}

    def start_vm(self, vm_id):
        qm = QEMUMachine(...)
        qm.launch()
        self._machines[vm_id] = qm  # Keep alive!
```

**Why**:

- `_qmp_connection` holds the asyncio server
- Socket cleanup happens in `__del__()` or `shutdown()`
- Losing the instance loses the QMP connection

### 2. Socket Files Are Ephemeral

**Don't try to reconnect via socket files**:

```python
# DOESN'T WORK
socket_path = "/tmp/vm.sock"
qm1 = QEMUMachine(monitor_address=socket_path)
qm1.launch()
# qm1 destroyed...

# Later, try to reconnect:
qm2 = QEMUMachine(monitor_address=socket_path)  # New instance
qm2._qmp.connect()  # FAILS - socket is owned by QEMU, not a server
```

**Why It Fails**:

- Original QEMUMonitorProtocol created server socket
- QEMU connected as client
- When QEMUMachine destroyed, server socket closed
- Socket file may still exist but is "dead"
- New QEMUMachine tries to create server → "Address already in use"

### 3. QMP Communication Flow

```
Python Process                    QEMU Process
--------------                    ------------
QEMUMonitorProtocol (server)
    |
    | create Unix socket
    | /tmp/vm.sock
    |
    | asyncio.start_unix_server()
    | listening...
    |                                   |
    |                                   | launch with:
    |                                   | -chardev socket,path=/tmp/vm.sock
    |                                   |
    | <----- connect() ----------------|
    |                                   |
    | accept()                          |
    |                                   |
    | <===== QMP Protocol ============>|
    |                                   |
    | cmd('query-status')               |
    | ------------------------------>   |
    | <----- {'return': {...}} ---------|
```

**Key Point**: Python is the SERVER, QEMU is the CLIENT. This is backwards from what you might expect!

### 4. Internal State to Check

```python
qm = QEMUMachine(monitor_address="/tmp/test.sock")
qm.launch()

# Check internal state
print(qm._monitor_address)        # "/tmp/test.sock"
print(qm._qmp_set)                # True (QMP enabled)
print(qm._qmp_connection)         # QEMUMonitorProtocol instance
print(qm._qmp_connection._address) # "/tmp/test.sock"
print(qm._qmp._server)            # asyncio.Server instance
print(qm._sock_pair)              # None (using Unix socket, not socketpair)
```

---

## Common Misconceptions

### Misconception 1: "QEMU creates the socket file"

**Reality**: Python creates the socket file (via asyncio). QEMU connects to it.

### Misconception 2: "Socket files persist and can be reused"

**Reality**: Socket files are tied to the QEMUMonitorProtocol server instance. When that's destroyed, the socket is unusable.

### Misconception 3: "You can reconnect to a running QEMU via socket file"

**Reality**: Only if you kept the original QEMUMachine instance alive. Creating a new instance won't work.

### Misconception 4: "monitor_address is where QEMU creates its socket"

**Reality**: monitor_address tells QEMUMonitorProtocol where to create its **server** socket. QEMU connects to it.

### Misconception 5: "Socket file not existing means QEMU failed to start"

**Reality**:

- With `monitor_address=None`, there's NO socket file (socketpair mode)
- With `monitor_address="/path"`, socket created by Python asyncio (may have timing issues in tests)
- Socket file existence is not a good health check

---

## Best Practices

### 1. Keep QEMUMachine Instances Alive

```python
class VMManager:
    def __init__(self):
        self._vms = {}  # vm_id → QEMUMachine instance

    def start(self, vm_id, config):
        qm = QEMUMachine(
            binary=config['binary'],
            args=config['args'],
            monitor_address=f"/var/run/vm-{vm_id}.sock"
        )
        qm.launch()
        self._vms[vm_id] = qm  # CRITICAL: Keep instance alive
        return qm.get_pid()

    def qmp_command(self, vm_id, command, **kwargs):
        qm = self._vms.get(vm_id)
        if not qm:
            raise ValueError(f"VM {vm_id} not managed by this instance")
        return qm.cmd(command, **kwargs)

    def stop(self, vm_id):
        qm = self._vms.pop(vm_id)
        if qm:
            qm.shutdown()  # Proper cleanup
```

### 2. Use QEMUMachine's Built-in Methods

```python
# GOOD - Direct API usage
qm = QEMUMachine(...)
qm.launch()
result = qm.cmd('query-status')
qm.shutdown()

# BAD - Trying to manage sockets manually
qm = QEMUMachine(...)
qm.launch()
socket_path = extract_socket_from_cmdline()
qmp_client = QMPClient()
qmp_client.connect(socket_path)  # Unnecessary complexity
```

### 3. Don't Rely on Socket Files for State

```python
# BAD
def is_vm_running(vm_id):
    socket_path = f"/var/run/vm-{vm_id}.sock"
    return os.path.exists(socket_path)  # Unreliable!

# GOOD
def is_vm_running(vm_id):
    qm = self._vms.get(vm_id)
    return qm is not None and qm.is_running()
```

### 4. Handle Process Restarts Gracefully

```python
class VMManager:
    def __init__(self):
        self._vms = {}
        self._load_running_vms()

    def _load_running_vms(self):
        """Load VMs from database."""
        for vm in db.get_running_vms():
            # Don't try to recreate QEMUMachine!
            # Just note that QMP is unavailable
            logger.warning(
                f"VM {vm.id} is running but QMP unavailable "
                f"(started in different process). "
                f"Stop and restart to enable QMP."
            )

    def qmp_command(self, vm_id, command):
        qm = self._vms.get(vm_id)
        if not qm:
            raise QMPUnavailable(
                f"QMP not available for VM {vm_id}. "
                f"VM may have been started in different process session."
            )
        return qm.cmd(command)
```

### 5. Prefer Socketpair Mode for Single-Process

```python
# If your application runs in one process, use socketpair
qm = QEMUMachine(
    binary='/usr/bin/qemu-system-x86_64',
    args=['-m', '128M'],
    monitor_address=None,  # Uses socketpair - no filesystem clutter
)
```

**Advantages**:

- No socket files to clean up
- No filesystem permissions issues
- Slightly faster (no Unix socket overhead)

**Disadvantages**:

- Can't reconnect from another process
- Can't inspect with `socat` or similar tools

---

## Testing Discoveries

### Why Socket Tests Failed Initially

```python
# This test SEEMED to fail:
socket_path = "/tmp/test.sock"
qm = QEMUMachine(monitor_address=socket_path)
qm.launch()
assert os.path.exists(socket_path)  # FAILED!
```

**Why**:

1. `launch()` calls `_pre_launch()` which calls `QEMUMonitorProtocol.__init__()`
2. `__init__()` calls `self._sync(self._qmp.start_server())`
3. `start_server()` uses `asyncio.start_unix_server()`
4. Socket creation happens in event loop
5. By the time `launch()` returns, socket JUST created
6. Filesystem might not have flushed the entry yet
7. Add `time.sleep(0.1)` and it works!

**Better Test**:

```python
socket_path = "/tmp/test.sock"
qm = QEMUMachine(monitor_address=socket_path)
qm.launch()

# Don't check file existence - check QMP works
result = qm.cmd('query-status')
assert result['return']['status'] == 'running'
```

### Debug Commands That Helped

```python
# Check if QMP connection established
qm._qmp_connection._qmp.greeting  # QMP greeting message

# Check server state
qm._qmp_connection._qmp._server  # asyncio.Server instance

# Get actual socket address
qm._qmp_connection._address

# Check if QMP set up
qm._qmp_set  # True/False

# Get QEMU command line
qm._qemu_full_args  # Tuple of all args
```

### Examining QEMU Process

```bash
# Get QEMU command line
cat /proc/<pid>/cmdline | tr '\0' '\n' | grep -A1 chardev

# Expected output:
-chardev
socket,id=mon,path=/tmp/test.sock
-mon
chardev=mon,mode=control

# Check open file descriptors
ls -la /proc/<pid>/fd/

# Expected to see:
# lrwx------ ... socket:[76222]  (the QMP socket)
```

---

## References

### Source Code Locations

- **QEMUMachine**: `qemu/python/qemu/machine/machine.py`
  - `__init__()`: Line ~150
  - `_pre_launch()`: Line ~336
  - `_build_launch_cmd()`: Line ~298

- **QEMUMonitorProtocol**: `qemu/python/qemu/qmp/legacy.py`
  - `__init__()`: Line ~79
  - Server mode check: Line ~93-95

- **QMPClient**: `qemu/python/qemu/qmp/protocol.py`
  - `start_server()`: Async method for socket server

### Key QEMU Documentation

- QMP Protocol: https://wiki.qemu.org/Documentation/QMP
- QEMU Monitor: https://qemu.readthedocs.io/en/latest/system/monitor.html
- Chardev: https://qemu.readthedocs.io/en/latest/system/invocation.html#character-device-options

---

## Conclusion

The QEMUMachine library is designed for **persistent connections** where the Python instance stays alive for the VM's lifetime. Attempting to reconnect via socket files or recreate instances leads to:

- Race conditions
- Socket ownership issues
- Lost QMP connections
- Cleanup problems

**The correct pattern**: Keep QEMUMachine instances in memory, use them directly for QMP, and only destroy them when the VM stops.

This aligns with QEMU's architecture where the Python side is the QMP **server** and QEMU is the **client**, creating an inversion that makes traditional socket-file-based reconnection patterns impossible.
