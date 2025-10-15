# Daemon Mode Removed

**Date**: 2025-10-10

## Summary

The daemon/DBus mode has been removed from MAQET due to a critical architectural flaw discovered during research.

## Reason for Removal

QEMUMachine objects require the Machine instance from the starting process. The daemon cannot provide working QMP functionality because:

1. VM started in one process creates QEMUMachine instance
2. Daemon running in different process cannot access that QEMUMachine
3. QMP commands from daemon fail silently or don't work at all
4. Daemon provided illusion of working while actually broken

See `DAEMON_ARCHITECTURE_RESEARCH.md` for detailed technical analysis.

## What Was Removed

- `maqet/daemon.py` (238 lines)
- `maqet/dbus_service.py` (425 lines)
- `tests/unit/test_daemon_unit.py` (629 lines)
- `docs/architecture/DBUS_DAEMON_ARCHITECTURE.md`
- `docs/deployment/maqetd.service`
- All daemon integration code from cli_generator.py and maqet.py
- All daemon references from CLAUDE.md

Total: 1,288+ lines of code removed.

## Migration Guide

### For QMP Users

**Before (broken daemon mode):**

```bash
maqet daemon start
maqet start myvm
maqet qmp myvm query-status  # Silently broken
```

**After (working Python API):**

```python
from maqet import Maqet

maqet = Maqet()
maqet.start("myvm")
result = maqet.qmp("myvm", "query-status")  # Works correctly
print(result)
```

### For CLI Users

CLI mode continues to work for all VM management commands:

- `maqet add`, `maqet start`, `maqet stop`, `maqet rm`
- `maqet ls`, `maqet status`, `maqet info`, `maqet inspect`
- `maqet snapshot` commands

QMP commands now require Python API for reliable operation.

## Documentation Status

Legacy daemon references remain in some documentation files:

- `docs/api/cli-reference.md` - Contains daemon command documentation
- `docs/api/python-api.md` - Contains daemon() method docs
- `docs/api/examples.md` - Contains daemon examples
- `docs/user-guide/qmp-commands.md` - Contains daemon mode section
- `docs/deployment/production.md` - Contains daemon deployment info

These will be updated in a future commit. For now, ignore any daemon-related documentation.

## Supported Operation Modes

1. **CLI Mode**: For VM lifecycle management (start, stop, status, etc.)
2. **Python API Mode**: For automation, QMP commands, and persistent operations

QMP commands work reliably only in Python API mode where Machine instances persist across method calls.
