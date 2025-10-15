# Unix Philosophy Change: Remove All Default Arguments

**Date**: 2025-10-12
**Status**: Implemented
**Impact**: Breaking change for configs relying on implicit defaults

## Problem Statement

MAQET was adding opinionated default arguments to every VM, violating Unix philosophy:

```python
# OLD apply_default_configuration() behavior:
- Default network: -netdev user,id=net0 -device virtio-net,netdev=net0
- Default memory: -m 2G
- Default CPU: -smp 1
```

### Why This Was Wrong

1. **Hides actual configuration**: Users don't see what's really running
2. **Causes bugs**: Network deduplication bug (commit 0d58eff) happened because defaults conflicted with user config
3. **Violates Unix philosophy**: "Provide mechanism, not policy"
4. **Makes debugging harder**: Users must understand both their config AND hidden defaults
5. **Opinionated without justification**: Why 2G RAM? Why virtio-net? These are arbitrary policy decisions

### The Unix Philosophy Argument

```bash
# QEMU itself runs perfectly fine with NO arguments:
qemu-system-x86_64

# QEMU uses sensible architecture-specific defaults:
# - Memory: 128MB (or default for architecture)
# - CPU: 1 core
# - Display: GTK/SDL if available, else none
# - Network: None (no network by default)
# - VGA: Default VGA for architecture
```

**If QEMU doesn't need defaults, why should maqet add them?**

## Solution: Remove All Opinionated Defaults

### What Changed

**File: maqet/config_handlers.py**

```python
# OLD: apply_default_configuration()
def apply_default_configuration(self):
    # Add default network if not specified
    has_network_config = self._has_network_arguments()
    if not has_network_config:
        self._qemu_machine.add_args(
            "-netdev", "user,id=net0",
            "-device", "virtio-net,netdev=net0",
        )

    # Set default memory if not specified
    if "memory" not in getattr(self, "config_data", {}):
        self._qemu_machine.add_args("-m", "2G")

    # Set default CPU if not specified
    if "cpu" not in getattr(self, "config_data", {}):
        self._qemu_machine.add_args("-smp", "1")

# NEW: apply_default_configuration()
def apply_default_configuration(self):
    """
    Apply minimal required configuration for maqet functionality.

    Philosophy: Provide mechanism, not policy (Unix philosophy).

    QEMU has perfectly good defaults. Maqet only adds arguments required
    for maqet itself to function (QMP socket, console setup).

    All other configuration comes from:
    1. User config (explicit)
    2. QEMU's own defaults (implicit)
    """
    pass  # QMP/console handled by MaqetQEMUMachine._base_args
```

### What Maqet Still Adds

Maqet ONLY adds arguments **required for maqet to function**:

- **QMP socket**: For maqet to communicate with QEMU (required)
- **Console setup**: For serial console access (required)

These are handled by `MaqetQEMUMachine._base_args` and are **mechanism**, not **policy**.

### Files Changed

1. **maqet/config_handlers.py**:
   - Removed `_has_network_arguments()` helper (no longer needed)
   - Replaced `apply_default_configuration()` with no-op and documentation
   - Removed all network, memory, CPU defaults

2. **tests/unit/test_network_deduplication.py**:
   - DELETED: Tests for network deduplication no longer relevant

3. **tests/unit/test_machine_unit.py**:
   - Updated 3 tests to verify NO defaults are added:
     - `test_configure_machine_basic`
     - `test_minimal_configuration`
     - `test_arguments_empty_list`

### Test Results

```
415 passed, 2 skipped, 1 warning in 32.63s
```

All tests pass with the new behavior.

## Migration Guide

### For Existing Configs

If your configs relied on implicit defaults, you must now be explicit:

```yaml
# OLD (implicit defaults):
name: myvm
binary: /usr/bin/qemu-system-x86_64
# Implicitly got: 2G RAM, 1 CPU, virtio-net network

# NEW (explicit configuration):
name: myvm
binary: /usr/bin/qemu-system-x86_64
arguments:
  - m: "2G"           # Explicit memory
  - smp: 1            # Explicit CPU
  - netdev: "user,id=net0"
  - device: "virtio-net,netdev=net0"
```

### Minimal Config (Uses QEMU Defaults)

```yaml
name: myvm
binary: /usr/bin/qemu-system-x86_64
# Uses QEMU's defaults: 128MB RAM, 1 CPU, no network, default VGA
```

## Philosophy

**Maqet provides mechanism (VM automation), not policy (default configurations).**

- Users who want 2G RAM: add `-m 2G` explicitly
- Users who want network: add `-netdev`/`-device` explicitly
- Users who want QEMU defaults: don't specify anything

This makes maqet:

1. **Transparent**: What you see is what you get
2. **Debuggable**: No hidden arguments
3. **Flexible**: Users decide policy
4. **Unix-compliant**: Mechanism, not policy

## Related Commits

- `1da17dd`: Fixed display handling (removed display/VGA defaults from MaqetQEMUMachine)
- `0d58eff`: Fixed network deduplication bug (bandaid for defaults problem)
- This commit: Removed ALL opinionated defaults (root cause fix)

## Future Work

Consider documenting QEMU's default behavior in user guide so users understand what happens when they don't specify arguments.
