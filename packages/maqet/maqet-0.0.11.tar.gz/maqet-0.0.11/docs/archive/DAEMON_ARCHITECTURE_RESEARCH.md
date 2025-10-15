# Daemon/DBus Architecture Research Report

**Date**: 2025-10-10
**Author**: AGENT-G (Architecture Research)
**Purpose**: Unbiased analysis of daemon/dbus implementation and recommendation

---

## Executive Summary

**Finding**: The daemon/dbus system IS implemented but has a CRITICAL architectural flaw that makes it largely useless.

**Problem**: QMP commands require the Machine instance from the process that started the VM. The daemon can start VMs, but if you start a VM directly (maqet start), QMP from daemon fails. If daemon starts VM, direct QMP fails.

**Recommendation**: **REMOVE daemon/dbus entirely** - it adds complexity without solving the actual problem.

---

## 1. Current Implementation Analysis

### 1.1 What Exists

The following components are fully implemented:

**daemon.py** (238 lines):

- DaemonManager class for lifecycle management (start/stop/status/restart)
- Daemonization with fork(), PID files, log redirection
- Signal handling and process management
- Integration with dbus_service

**dbus_service.py** (425 lines):

- MaqetDBusService class with full DBus implementation
- Exposes all VM methods: add, start, stop, ls, status
- Exposes all QMP methods: qmp, qmp_key, qmp_type, qmp_stop, qmp_cont
- Health check (ping), machine count tracking
- Zombie process reaping (SIGCHLD handler + periodic reaper)

**Integration points**:

- maqet.py:1520-1564: `daemon()` @api_method (start/stop/status/restart)
- cli_generator.py:461-582: `_try_dbus_execution()` - auto-routes QMP/VM commands to daemon if running
- Tests: test_daemon_unit.py (600+ lines of comprehensive tests)

### 1.2 What It Does

**Daemon mode workflow**:

1. User runs: `maqet daemon start`
2. Daemon forks to background, creates PID file
3. Daemon holds persistent Maqet() instance with Machine registry
4. CLI commands check `check_daemon_running()` before execution
5. If daemon available: route command via DBus
6. If daemon unavailable: execute directly

**DBus interface**:

- Service: com.maqet.Manager
- Object: /com/maqet/Manager
- Interface: com.maqet.Manager
- Transport: Session bus

### 1.3 Is It Actually Used?

**YES** - it is used when available:

```python
# cli_generator.py:478-482
from ..dbus_service import check_daemon_running, get_dbus_client

if not check_daemon_running():
    return (False, None)  # Fall back to direct execution

client = get_dbus_client()
# ... route command via DBus ...
```

**Automatic fallback**: If daemon not running, CLI uses direct execution.

---

## 2. The Critical Architectural Flaw

### 2.1 The Problem

**QMP requires the Machine instance from the VM's starting process**:

```python
# maqet.py:1017-1025
machine = self._machines.get(vm.id)
if not machine:
    # Machine not in dict - VM was started in different process
    # QMP not available without the original QEMUMachine instance
    raise MaqetError(
        f"QMP not available for VM '{vm_id}' - VM was started in a "
        "different process session. Stop and restart the VM to enable QMP."
    )
```

**Why this happens**:

- `self._machines` is an in-memory dict in the Maqet instance
- QEMUMachine holds QMP socket connection state
- When VM started by daemon, daemon's Maqet instance has the Machine
- When VM started directly, CLI's Maqet instance has the Machine
- No Machine object = No QMP access

### 2.2 Concrete Failure Scenarios

**Scenario 1: User starts VM directly**

```bash
maqet start myvm           # Works - direct execution
maqet daemon start         # Start daemon
maqet qmp myvm query-status  # FAILS - daemon has no Machine for this VM
```

**Scenario 2: Daemon starts VM**

```bash
maqet daemon start         # Start daemon
maqet start myvm           # Routed to daemon, VM started there
maqet daemon stop          # Daemon stopped
maqet qmp myvm query-status  # FAILS - Machine instance was in dead daemon
```

**Scenario 3: Mixed usage**

```bash
maqet start vm1            # Direct
maqet daemon start         # Start daemon
maqet start vm2            # Routed to daemon
maqet qmp vm1 ...          # FAILS (Machine in direct CLI, but routed to daemon)
maqet qmp vm2 ...          # Works (Machine in daemon)
```

### 2.3 User's Insight

From MANUAL_TESTS_AND_REVIEW.md:
> "Cannot understand the purpose of the daemon and dbus. Dbus we need for interprocess communication - and we have one - communication between maqet cli and actual Machine running (it's PID written in maqet DB file). So why we need daemon?"

**User is 100% correct**: The PID is already stored in the database (state.py). We already have IPC capability via the QMP socket that QEMU creates.

---

## 3. Research Questions Answered

### 3.1 Is daemon mode actually implemented and used?

**YES** - fully implemented and automatically used when daemon is running.

### 3.2 Can we communicate with QEMU VMs without daemon?

**YES** - this is how it currently works when daemon is not running:

1. VM stores socket_path in database (state.py)
2. Machine instance connects to QMP socket
3. QMP commands work fine

**The problem**: Machine instance must exist in the calling process's memory.

### 3.3 What's the benefit of daemon vs direct VM communication?

**Theoretical benefit**: Persistent Machine instances for all VMs, enabling QMP across CLI invocations.

**Actual benefit**: NONE - due to the architectural flaw above. You can't mix daemon and direct usage.

### 3.4 Why can't each VM be a dbus client?

**Excellent question from user**. Let's analyze:

**Current architecture**:

- Daemon = DBus service
- CLI = DBus client
- VM = QEMU process (not DBus-aware)

**Alternative architecture** (user's idea):

- Each VM = DBus service (one service per VM)
- CLI = DBus client to any VM
- No global daemon needed

**Why this would work better**:

1. Each VM process could export its own DBus interface
2. CLI would connect directly to the VM's DBus service
3. No dependency on daemon being up/down
4. No Machine instance sharing problem

**Implementation**: Would require wrapping QEMU with a Python process that:

- Starts QEMU as subprocess
- Holds the Machine instance
- Exports DBus interface for that specific VM
- Lives as long as VM lives

This is essentially what systemd does with systemd-run.

### 3.5 Alternative IPC Mechanisms

**Option 1: Direct QMP socket communication** (RECOMMENDED)

- QMP socket path stored in database (already done)
- CLI connects directly to QMP socket via python-qemu library
- No daemon needed
- Works across processes

**Problem**: Current QEMUMachine abstraction doesn't support reconnecting to existing sockets.

**Solution**: Enhance QEMUMachine or create QMPClient class that can:

```python
# Pseudo-code
vm = state_manager.get_vm("myvm")
qmp_client = QMPClient(vm.socket_path)
result = qmp_client.execute("query-status")
```

**Option 2: Each VM as separate DBus service**

- Each VM exports its own DBus service
- No global daemon
- CLI discovers VM services via session bus
- Good isolation

**Option 3: Unix domain sockets with custom protocol**

- Similar to QMP but our own protocol
- More control but more work
- Reinventing the wheel

**Option 4: Shared memory**

- Overkill for command/response pattern
- Harder to implement correctly

---

## 4. Code Evidence

### 4.1 Daemon IS Implemented

**daemon.py exists**: 238 lines, fully functional
**dbus_service.py exists**: 425 lines, full DBus integration
**CLI integration exists**: cli_generator.py automatically routes to daemon
**Tests exist**: test_daemon_unit.py with 600+ lines

### 4.2 QMP Limitation Documented in Code

```python
# maqet.py:1020-1025
if not machine:
    # Machine not in dict - VM was started in different process
    # QMP not available without the original QEMUMachine instance
    raise MaqetError(
        f"QMP not available for VM '{vm_id}' - VM was started in a "
        "different process session. Stop and restart the VM to enable QMP."
    )
```

This error message proves the developers knew about the limitation.

### 4.3 Database Already Has What We Need

```python
# state.py:64-68
@dataclass
class VMInstance:
    id: str
    name: str
    # ...
    pid: Optional[int]           # <-- Process ID
    socket_path: Optional[str]   # <-- QMP socket path
```

We already store PID and socket_path. This is sufficient for IPC.

---

## 5. Recommendation

### 5.1 Decision: REMOVE Daemon/DBus Entirely

**Reasoning**:

1. **Does not solve the problem**: Due to Machine instance limitation, daemon is useless for mixed usage patterns
2. **Adds complexity**: 663 lines of code (daemon.py + dbus_service.py) + dependencies (dbus-python, PyGObject)
3. **User confusion**: "Cannot understand the purpose" - architecture is not intuitive
4. **Better alternatives exist**: Direct QMP socket connection
5. **Not production-ready**: The error message "Stop and restart the VM" is a workaround, not a solution

### 5.2 Proposed Architecture

**Phase 1: Remove daemon/dbus** (immediate)

- Delete daemon.py, dbus_service.py
- Remove daemon() API method
- Remove _try_dbus_execution() from cli_generator.py
- Remove test_daemon_unit.py
- Remove dbus-python, PyGObject from dependencies
- Update CLAUDE.md to remove daemon references

**Phase 2: Implement direct QMP reconnection** (future)

- Create QMPClient class that can connect to existing socket
- Use state.socket_path to reconnect
- Works across CLI invocations
- No daemon needed

```python
# Proposed implementation
class QMPClient:
    def __init__(self, socket_path: str):
        self.socket_path = socket_path
        # Connect to existing QMP socket

    def execute(self, command: str, **kwargs):
        # Send QMP command, return response
```

Then in maqet.py:

```python
def qmp(self, vm_id: str, command: str, **kwargs):
    vm = self.state_manager.get_vm(vm_id)
    if not vm or vm.status != "running":
        raise MaqetError(...)

    # Connect directly to QMP socket (no Machine instance needed)
    client = QMPClient(vm.socket_path)
    return client.execute(command, **kwargs)
```

### 5.3 Migration Path

**Backward compatibility**: None needed - daemon was optional and caused more problems than it solved.

**User impact**:

- Simplified architecture
- No more "VM started in different process" errors
- Remove confusing `maqet daemon start/stop` commands
- Reduce dependencies

**Documentation**: Update docs to explain:

1. QMP works via direct socket connection
2. No daemon needed
3. QMP works across CLI invocations (after Phase 2)

---

## 6. What to Clean Up

### 6.1 Files to Delete

```
maqet/daemon.py                          (238 lines)
maqet/dbus_service.py                    (425 lines)
tests/unit/test_daemon_unit.py           (600+ lines)
```

### 6.2 Code to Remove

**maqet/maqet.py**:

- Lines 1520-1564: `daemon()` method
- Lines 1528: `from .daemon import DaemonManager`

**maqet/generators/cli_generator.py**:

- Lines 461-582: `_try_dbus_execution()` method
- Lines 477-484: daemon imports and checks
- Lines 188-193: Remove DBus routing from `_execute_method()`

**maqet/**init**.py** (if daemon exported):

- Remove daemon imports

**pyproject.toml / requirements.txt**:

- Remove: dbus-python
- Remove: PyGObject

### 6.3 CLAUDE.md Lines to Remove

Search for and remove lines containing:

- "daemon mode"
- "daemon" (context-dependent)
- "RECOMMENDED for QMP"
- "Best of both worlds"
- "DBus service"
- "Long-running background process"
- "CLI communicates with daemon via DBus"
- "QMP works across CLI invocations" (only in daemon context)

Specifically from CLAUDE.md (approximate line numbers, need verification):

- Section about daemon mode being "RECOMMENDED"
- Examples showing `maqet daemon start`
- Documentation claiming daemon enables persistent QMP

### 6.4 Docstrings to Clean

**maqet/maqet.py**:

- Line 82: "TODO: Does daemon mode still exist? If not - clean up docstrings and docs"
  - Answer: YES it exists, but we're removing it. Update this TODO to track removal.

**maqet/machine.py**:

- Lines 90-94: "NOTE: Good - atexit handler prevents orphaned QEMU processes..."
  - Keep this - it's still needed without daemon

---

## 7. Pros and Cons Analysis

### 7.1 Keep Daemon/DBus

**Pros**:

- Already implemented (663 lines)
- Well-tested (600+ test lines)
- Follows daemon pattern (like systemd)
- Theoretically elegant architecture

**Cons**:

- Does not work for mixed usage (critical flaw)
- Adds 2 dependencies (dbus-python, PyGObject)
- Complex for minimal benefit
- User confusion ("cannot understand purpose")
- Error message admits limitation ("Stop and restart VM")
- Incompatible with most common workflow (start VM directly, use QMP)

### 7.2 Remove Daemon/DBus

**Pros**:

- Simpler architecture
- Remove 1263+ lines of code
- Remove 2 dependencies
- No "started in different process" errors
- Easier to understand
- Aligns with user's intuition

**Cons**:

- Loss of implemented code (sunk cost)
- Need to implement Phase 2 (QMP reconnection) eventually
- Daemon pattern is "proper" Linux architecture (but not needed here)

### 7.3 Redesign (Each VM as DBus Client)

**Pros**:

- Solves Machine instance problem
- Better isolation (VM = service)
- No global daemon dependency
- Could work across reboots

**Cons**:

- Major redesign required
- Adds complexity to VM startup
- Still requires DBus dependencies
- Overkill for QMP command/response pattern

---

## 8. Evidence-Based Conclusion

### 8.1 Objective Facts

1. **Daemon is implemented** - 663 lines of working code
2. **Daemon has critical flaw** - cannot mix daemon and direct usage
3. **Database already has IPC data** - PID and socket_path stored
4. **Direct QMP is simpler** - one socket, one connection, works everywhere
5. **User is confused** - "cannot understand the purpose"

### 8.2 Recommendation Justification

**Remove daemon/dbus because**:

1. Architectural flaw makes it mostly useless
2. Adds unnecessary complexity
3. Better solution exists (direct QMP)
4. User feedback is negative
5. Reduces dependencies and code

**This is not a "nice to have"** - the daemon is **actively harmful** because:

- It creates the illusion of working QMP across processes
- Falls back silently when it doesn't work
- Error message blames user ("Stop and restart VM")
- Confuses users about how maqet works

### 8.3 Implementation Priority

**P0 (Do Now)**: Remove daemon/dbus

- Delete files
- Remove integrations
- Update docs
- Reduce dependencies

**P1 (Do Soon)**: Implement direct QMP

- Create QMPClient class
- Use socket_path for reconnection
- Works across CLI invocations

**P2 (Consider Later)**: Enhanced features

- QMP connection pooling
- Async QMP operations
- QMP event monitoring

---

## 9. Final Answer to User's Question

**User asked**: "Why can't we make every VM a dbus client?"

**Answer**: We don't need DBus at all. QEMU already provides QMP sockets for IPC. We store the socket path in the database. We just need to connect to it directly instead of going through a daemon.

**User insight**: "We have IPC - communication between maqet cli and actual Machine running (it's PID written in maqet DB file)."

**User is correct**: The database IS the IPC mechanism. It stores:

- VM status (running/stopped)
- Process ID (for process management)
- Socket path (for QMP communication)

This is all we need. Daemon/dbus is redundant.

---

## 10. Recommended Actions

### For AGENT-F (Documentation)

When you clean up docstrings and CLAUDE.md:

1. **Search for these terms** and remove associated content:
   - "daemon mode"
   - "DBus service"
   - "RECOMMENDED for QMP"
   - "Best of both worlds"
   - "maqetd"
   - "com.maqet.Manager"

2. **Keep these sections** (they're still valid):
   - QMP communication basics
   - StateManager and database
   - Direct VM process management
   - atexit cleanup handlers

3. **Add note to CLAUDE.md**:

   ```
   ## QMP Communication

   QMP commands work by connecting directly to the VM's QMP socket. The socket
   path is stored in the database when the VM starts. CLI commands can execute
   QMP operations on any running VM by connecting to its socket.

   No daemon needed - direct socket communication works across CLI invocations.
   ```

### For Future Implementation

When implementing Phase 2 (direct QMP):

1. Create `maqet/qmp_client.py` with QMPClient class
2. Replace Machine-based QMP with socket-based QMP
3. Test QMP across multiple CLI invocations
4. Verify no regression in QMP functionality

---

## Appendix: Code Statistics

**Daemon/DBus Implementation**:

- daemon.py: 238 lines
- dbus_service.py: 425 lines
- test_daemon_unit.py: 600+ lines
- Integration code: ~100 lines
- **Total**: ~1363 lines to remove

**Dependencies to Remove**:

- dbus-python
- PyGObject (unless used elsewhere)

**Files to Modify**:

- maqet/maqet.py
- maqet/generators/cli_generator.py
- maqet/CLAUDE.md
- pyproject.toml / requirements.txt

---

**End of Report**

**Summary**: Daemon/dbus is fully implemented but architecturally flawed. It cannot solve the QMP persistence problem due to Machine instance limitations. Recommendation: REMOVE entirely and implement direct QMP socket reconnection. User's intuition is correct - database already provides necessary IPC.
