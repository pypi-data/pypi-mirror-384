# Architectural Review - Decision Document

**Date**: 2025-10-10
**Reviewer**: m4x0n
**Source**: ARCHITECTURAL_REVIEW.md

---

## How to Use This Document

For each issue below:

1. Review the problem description and recommendation
2. Choose one decision option (mark with X)
3. Add any notes or alternative solutions
4. Return completed document for implementation

**Decision Options**:

- `[ ] APPROVE` - Implement as recommended
- `[ ] APPROVE_MODIFIED` - Implement with changes (specify in notes)
- `[ ] DEFER` - Not for current release
- `[ ] REJECT` - Will not implement

---

## CRITICAL ISSUES (Must Review for 1.0)

### Issue #1: Cross-Process QMP Communication Impossible

**Priority**: CRITICAL
**Location**: `maqet/machine.py:129-158`
**Category**: ARCH

**Problem**:
QMP commands don't work in CLI mode because QEMUMachine instances cannot cross process boundaries. When CLI exits, QMP connections are destroyed.

**Impact**:

- Major feature limitation: `maqet qmp myvm query-status` fails
- Confusing UX: Users expect QMP to work but get errors
- Only works in Python API mode (same process)

**Recommended Solution**:
Implement direct socket communication for v1.0:

- Bypass QEMUMachine, talk directly to QMP socket
- Store socket path in database, connect on demand
- No daemon needed, simpler architecture

**Alternative Solutions**:

1. Daemon mode (complex, 1-2 weeks)
2. Hybrid approach (very complex, 2-3 weeks)

**Effort**: Medium (2-4 days)

**DECISION**:

- [x] APPROVE - Direct socket for v1.0
- [ ] APPROVE_MODIFIED - (specify changes below)
- [ ] DEFER - Not for v1.0
- [ ] REJECT - Will not implement

**Notes**:

```

```

---

### Issue #2: God Object Pattern in Maqet Class

**Priority**: CRITICAL
**Location**: `maqet/maqet.py:35-1496`
**Category**: ARCH

**Problem**:
Maqet class is 1,496 lines handling everything:

- VM lifecycle (add, start, stop, rm)
- QMP commands (qmp, keys, type, screendump)
- Storage/snapshots
- State management
- CLI/API coordination
- Configuration

**Impact**:

- Hard to maintain and understand
- Difficult to test (many dependencies)
- Hard to extend without modifying god object
- Tight coupling prevents code reuse

**Recommended Solution**:
Refactor into managers:

```python
class Maqet:
    def __init__(self):
        self.vm_manager = VMManager()        # VM lifecycle
        self.qmp_manager = QMPManager()      # QMP operations
        self.snapshot_manager = SnapshotCoordinator()
        self.config_parser = ConfigParser()
```

**Benefits**:

- Single responsibility per manager
- Easier to test (mock one manager)
- Maintainable file sizes (<500 lines)
- Better organization

**Effort**: Large (1-2 weeks, can be incremental)

**DECISION**:

- [x] APPROVE - Refactor as recommended
- [ ] APPROVE_MODIFIED - (specify approach below)
- [ ] DEFER - Not for v1.0
- [ ] REJECT - Keep as is

**Notes**:

```

```

---

## HIGH PRIORITY ISSUES (Should Fix for 1.0)

### Issue #3: Inconsistent Error Handling Strategy

**Priority**: HIGH
**Location**: Multiple files
**Category**: MAINTAIN

**Problem**:
Error handling varies across codebase:

- Some wrap exceptions (MaqetError, MachineError)
- Others let them propagate
- Some use bare `except Exception` (too broad)
- Error message quality inconsistent

**Recommended Solution**:

1. Create exception hierarchy:
   - ConfigurationError
   - VMLifecycleError
   - QMPError
2. Document when to use each
3. Always provide actionable error messages
4. Never use bare `except Exception`

**Effort**: Medium (3-5 days)

**DECISION**:

- [x] APPROVE
- [ ] APPROVE_MODIFIED
- [ ] DEFER
- [ ] REJECT

**Notes**:

```

```

---

### Issue #4: Machine Class Too Many Responsibilities

**Priority**: HIGH
**Location**: `maqet/machine.py:121-907`
**Category**: ARCH

**Problem**:
Machine class (907 lines) handles:

- QEMU process lifecycle
- Configuration validation
- QMP communication
- Storage setup
- Config handler registry
- Signal handling

**Recommended Solution**:
Extract responsibilities:

- QMPClient class (QMP only)
- ConfigValidator class (validation only)
- StorageCoordinator class (storage only)

**Effort**: Large (1 week)

**DECISION**:

- [x] APPROVE
- [ ] APPROVE_MODIFIED
- [ ] DEFER
- [ ] REJECT

**Notes**:

```

```

---

### Issue #5: Global Mutable State in Registries

**Priority**: HIGH
**Location**: `maqet/config_handlers.py:48`, `maqet/api/decorators.py:11`
**Category**: ARCH

**Problem**:
Global module-level registries:

- Tests interfere with each other
- Cannot have multiple Maqet instances with different configs
- Parallel test execution unreliable

**Recommended Solution**:
Make registries instance-based:

```python
class Maqet:
    def __init__(self):
        self.api_registry = APIRegistry()      # INSTANCE
        self.config_registry = ConfigHandlerRegistry()
```

**Effort**: Medium (4-6 days, requires refactoring decorators)

**DECISION**:

- [x] APPROVE
- [ ] APPROVE_MODIFIED
- [ ] DEFER
- [ ] REJECT

**Notes**:

```

```

---

### Issue #6: SQLite Connection Management Race Conditions

**Priority**: HIGH
**Location**: `maqet/state.py:260-324`
**Category**: PERF

**Problem**:

- Retry logic may not be enough under high load
- No connection pooling (opens connection per operation)
- Race conditions possible with multiple processes

**Recommended Solution**:
Implement connection pooling with threading.Lock

**Alternative**: Switch to PostgreSQL for production

**Effort**: Medium (3-4 days)

**DECISION**:

- [x] APPROVE - Connection pooling
- [ ] APPROVE_MODIFIED
- [ ] DEFER
- [ ] REJECT

**Notes**:

```

```

---

### Issue #7: Snapshot Operations Block

**Priority**: HIGH
**Location**: `maqet/snapshot.py:56-108`
**Category**: PERF

**Problem**:
Synchronous subprocess.run() blocks for large disks:

- CLI freezes during snapshot operations
- No progress indication
- Cannot cancel

**Recommended Solution**:
Add progress reporting (1-2 days):

- Progress callback parameter
- "Still working..." messages every 30s
- Estimated time remaining

**Alternative**: Full async implementation (3-5 days)

**Effort**: Small for progress, Medium for async

**DECISION**:

- [ ] APPROVE - Progress reporting only
- [ ] APPROVE - Full async
- [x] DEFER - Not critical for v1.0
- [ ] REJECT

**Notes**:

```

```

---

### Issue #8: Missing Import Validation

**Priority**: HIGH
**Location**: Multiple files
**Category**: MAINTAIN

**Problem**:
Optional imports (psutil) may fail at runtime with unclear errors

**Recommended Solution**:

1. Document optional dependencies in README
2. Provide clear error messages when missing
3. Use TYPE_CHECKING for optional type hints

**Effort**: Small (1-2 hours)

**DECISION**:

- [x] APPROVE
- [ ] APPROVE_MODIFIED
- [ ] DEFER
- [ ] REJECT

**Notes**:

```

```

---

### Issue #9: ConfigHandler System Lacks Discovery

**Priority**: HIGH
**Location**: `maqet/config_handlers.py:52-69`
**Category**: MAINTAIN

**Problem**:

- No way to list registered handlers (debugging)
- No validation that critical handlers exist
- Typos in config keys silently ignored

**Recommended Solution**:

1. Add `get_registered_handlers()` for debugging
2. Validate critical handlers at startup
3. Optional strict mode (fail on unknown keys)

**Effort**: Small (2-3 hours)

**DECISION**:

- [x] APPROVE
- [ ] APPROVE_MODIFIED
- [ ] DEFER
- [ ] REJECT

**Notes**:

```

```

---

## MEDIUM PRIORITY ISSUES (Consider for v1.0 or defer to v1.1)

### Issue #10: Duplicate Code in Global Options

**Priority**: MEDIUM
**Location**: `maqet/generators/cli_generator.py:187-241`
**Category**: REFACTOR

**Problem**: Global options code duplicated (main parser + parent parser)

**Solution**: Extract to `_add_global_options(parser)` method

**Effort**: Small (<1 hour)

**DECISION**:

- [x] APPROVE
- [ ] DEFER
- [ ] REJECT

**Notes**:

```

```

---

### Issue #11: Magic Numbers in Timeout/Retry Logic

**Priority**: MEDIUM
**Location**: Multiple files
**Category**: MAINTAIN

**Problem**: Hardcoded timeouts scattered (0.1s, 30s, 2s, 300s)

**Solution**: Create constants.py with Timeouts and Retries classes

**Effort**: Small (1-2 hours)

**DECISION**:

- [x] APPROVE
- [ ] DEFER
- [ ] REJECT

**Notes**:

```

```

---

### Issue #12: Inconsistent Path Handling (str vs Path)

**Priority**: MEDIUM
**Location**: Multiple files
**Category**: MAINTAIN

**Problem**: Some functions use str, others use pathlib.Path

**Solution**: Standardize on pathlib.Path internally, convert to str at boundaries

**Effort**: Medium (2-3 days)

**DECISION**:

- [x] APPROVE
- [ ] DEFER
- [ ] REJECT

**Notes**:

```

```

---

### Issue #13: _format_nested_value Too Complex

**Priority**: MEDIUM
**Location**: `maqet/config_handlers.py:218-319`
**Category**: REFACTOR

**Problem**: 101-line recursive method with high cyclomatic complexity

**Solution**: Break into smaller methods (_format_empty_value,_format_primitive, etc.)

**Effort**: Small (2-3 hours)

**DECISION**:

- [x] APPROVE
- [ ] DEFER
- [ ] REJECT

**Notes**:

```

```

---

### Issue #14: No Centralized Defaults

**Priority**: MEDIUM
**Location**: `maqet/config_handlers.py:495`, `maqet/machine.py:496`
**Category**: MAINTAIN

**Problem**: Default values scattered (memory: 2G, cpu: 1, binary path)

**Solution**: Create defaults.py with Defaults class

**Effort**: Small (1-2 hours)

**DECISION**:

- [ ] APPROVE
- [x] DEFER
- [ ] REJECT

**Notes**:

```

Memory and cpu not stated - qemu binary runs w/o arguments. Why we need defaults at all?

```

---

### Issue #15: Test Fixtures Not Shared

**Priority**: MEDIUM
**Location**: `tests/fixtures/`, conftest.py files
**Category**: TEST

**Problem**: Each test type has duplicate fixtures (temp_data_dir, mocks, configs)

**Solution**: Create shared fixtures in root tests/conftest.py

**Effort**: Small (2-3 hours)

**DECISION**:

- [x] APPROVE
- [ ] DEFER
- [ ] REJECT

**Notes**:

```

```

---

### Issue #16: Long Methods in Maqet Class

**Priority**: MEDIUM
**Location**: `maqet/maqet.py:203-351`, `maqet/maqet.py:568-666`
**Category**: REFACTOR

**Problem**: add() is 149 lines, _remove_all_vms() is 98 lines

**Solution**: Extract helper methods

**Effort**: Medium (1-2 days)

**DECISION**:

- [ ] APPROVE
- [x] DEFER
- [ ] REJECT

**Notes**:

```

```

---

### Issue #17: No VM Name Conflict Validation

**Priority**: MEDIUM
**Location**: `maqet/state.py:326-418`
**Category**: MAINTAIN

**Problem**: Name conflicts only caught by SQLite, error message is database error

**Solution**: Check name exists before inserting, provide helpful error message

**Effort**: Small (30 minutes)

**DECISION**:

- [x] APPROVE
- [ ] DEFER
- [ ] REJECT

**Notes**:

```

```

---

### Issue #18: No QEMU Binary Health Check

**Priority**: MEDIUM
**Location**: `maqet/machine.py:493-513`
**Category**: MAINTAIN

**Problem**: Only checks if binary exists, not if it works

**Solution**: Run `qemu --version` to validate binary

**Effort**: Small (1 hour)

**DECISION**:

- [x] APPROVE
- [ ] DEFER
- [ ] REJECT

**Notes**:

```

```

---

## LOW PRIORITY ISSUES (Technical Debt - defer to v1.1+)

### Issue #19: Outdated Daemon Comments

**Priority**: LOW
**Location**: `maqet/machine.py:129-158`

**Problem**: Comment references removed daemon mode

**Solution**: Update comment to reflect current state

**Effort**: Small (15 minutes)

**DECISION**:

- [x] APPROVE
- [ ] DEFER
- [ ] REJECT

---

### Issue #20: No Metrics/Telemetry

**Priority**: LOW
**Location**: N/A (missing feature)

**Problem**: No performance tracking (start times, latencies, durations)

**Solution**: Add optional metrics tracking

**Effort**: Medium (2-3 days)

**DECISION**:

- [ ] APPROVE
- [x] DEFER
- [ ] REJECT

---

### Issue #21: Test Naming Inconsistency

**Priority**: LOW
**Location**: tests/ (multiple)

**Problem**: Inconsistent test method naming patterns

**Solution**: Standardize on test_<method>_<scenario>_<expected>()

**Effort**: Small (1-2 hours, can automate)

**DECISION**:

- [x] APPROVE
- [ ] DEFER
- [ ] REJECT

---

### Issue #22: No Storage Plugin Documentation

**Priority**: LOW
**Location**: `maqet/storage.py`

**Problem**: Plugin architecture exists but not documented

**Solution**: Add docstring with examples for adding new storage types

**Effort**: Small (1 hour)

**DECISION**:

- [x] APPROVE
- [ ] DEFER
- [ ] REJECT

---

### Issue #23: No Performance Tests

**Priority**: LOW
**Location**: tests/ (missing)

**Problem**: No benchmarks for VM start time, snapshot speed, etc.

**Solution**: Add performance test suite with @pytest.mark.performance

**Effort**: Medium (2-3 days)

**DECISION**:

- [x] APPROVE
- [ ] DEFER
- [ ] REJECT

---

## SUMMARY FOR REVIEW

**Total Issues**: 23

- Critical: 2
- High: 7
- Medium: 9
- Low: 5

### Recommended for v1.0 (Must Fix)

1. Issue #1 - QMP cross-process (CRITICAL)
2. Issue #2 - God object refactoring (CRITICAL)
3. Issues #3-#9 - High priority architectural issues

**Estimated Total Effort for v1.0 Recommendations**: 7-10 weeks

### Quick Wins (Small effort, high impact)

- Issue #8: Import validation (1-2 hours)
- Issue #9: Handler discovery (2-3 hours)
- Issue #17: VM name validation (30 min)
- Issue #18: QEMU health check (1 hour)

### Can Defer to v1.1+

- Issues #10-#23 (Medium and Low priority)
- Total: 14 issues

---

## APPROVAL SUMMARY

**Total Approved**: 18
**Total Deferred**: 4
**Total Rejected**: 0

**Priority for Implementation**:

1. Phase 1: Quick wins (Issues #8, #9, #17, #18, #19) - 1 week
2. Phase 4: QMP cross-process (Issue #1) - CRITICAL - 2 weeks
3. Phase 3: Error handling (Issue #3) - 1 week
4. Phase 6: Global state (Issue #5) - 2 weeks
5. Phase 8: God object refactoring (Issue #2) - 4 weeks

**Target Release for Approved Items**:

- v1.0: Issues #1-6, #8-13, #15, #17-19, #21-23 (18 approved)
- v1.1: Issues #7, #14, #16, #20 (4 deferred)
- v2.0: N/A

**Timeline**: 14 weeks for full implementation (see IMPLEMENTATION_PLAN.md)

**Additional Notes**:

```
Issue #14 (Defaults) deferred pending review:
- User questions need for defaults if QEMU runs without them
- Current defaults (2G RAM, 1 CPU) more reasonable than QEMU's (128MB)
- Will revisit after v1.0 based on user feedback

All approved items have detailed implementation plan in IMPLEMENTATION_PLAN.md
with 8 phases, dependency graph, and timeline.
```

**Signature**: m4x0n  **Date**: 2025-10-10
