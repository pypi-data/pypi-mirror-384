# Troubleshooting Guide

Common issues and solutions for MAQET virtual machine management.

## Table of Contents

- [Installation Issues](#installation-issues)
- [VM Start Failures](#vm-start-failures)
- [Display Issues](#display-issues)
- [QMP Connection Issues](#qmp-connection-issues)
- [Storage Issues](#storage-issues)
- [Performance Problems](#performance-problems)
- [Database and State Issues](#database-and-state-issues)
- [Debugging Techniques](#debugging-techniques)
- [Getting Help](#getting-help)

---

## Installation Issues

### Issue: "command not found: maqet"

**Symptom**: After installation, `maqet` command not found in shell.

**Diagnosis**:

```bash
# Check if maqet is installed
pip list | grep maqet

# Check where pip installs scripts
python3 -m site --user-base
```

**Cause**: Python scripts directory not in PATH.

**Solution**:

Add Python scripts directory to PATH:

```bash
# Check current PATH
echo $PATH

# Add user base bin to PATH (typically ~/.local/bin)
export PATH="$HOME/.local/bin:$PATH"

# Make permanent (bash)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Make permanent (zsh)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

Verify:

```bash
which maqet
maqet --version
```

### Issue: "ModuleNotFoundError: No module named 'maqet'"

**Symptom**: Python cannot find maqet module.

**Diagnosis**:

```bash
# Check if installed
pip list | grep maqet

# Check Python version
python3 --version

# Check which python pip is using
pip --version
```

**Causes**:

1. MAQET not installed
2. Using wrong Python environment
3. Virtual environment not activated

**Solution 1 - Install MAQET**:

```bash
pip install maqet
```

**Solution 2 - Activate Virtual Environment**:

```bash
source ~/.venvs/maqet/bin/activate
pip list | grep maqet
```

**Solution 3 - Use Correct Python**:

```bash
# If you have multiple Python versions
python3.12 -m pip install maqet
python3.12 -m maqet --version
```

### Issue: "ERROR: Could not find a version that satisfies the requirement"

**Symptom**: Pip cannot install maqet.

**Diagnosis**:

```bash
python3 --version
```

**Cause**: Python version too old (MAQET requires Python 3.12+).

**Solution**:

Install Python 3.12 or higher:

**Ubuntu/Debian**:

```bash
sudo apt update
sudo apt install python3.12 python3.12-venv
```

**Fedora**:

```bash
sudo dnf install python3.12
```

Then use the correct Python version:

```bash
python3.12 -m pip install maqet
python3.12 -m maqet --version
```

### Issue: Permission errors during installation

**Symptom**: `PermissionError` or `Access denied` during pip install.

**Causes**:

1. Trying to install globally without sudo
2. System-managed Python

**Solution 1 - User Install**:

```bash
pip install --user maqet
```

**Solution 2 - Virtual Environment** (Recommended):

```bash
python3 -m venv ~/.venvs/maqet
source ~/.venvs/maqet/bin/activate
pip install maqet
```

**Solution 3 - System Install** (Not Recommended):

```bash
sudo pip install maqet
```

---

## VM Start Failures

### Issue: VM won't start - QEMU binary not found

**Symptom**: `ERROR: QEMU binary not found: /usr/bin/qemu-system-x86_64`

**Diagnosis**:

```bash
# Check if QEMU installed
which qemu-system-x86_64

# List available QEMU binaries
ls /usr/bin/qemu-system-*
```

**Cause**: QEMU not installed or binary path incorrect.

**Solution 1 - Install QEMU**:

**Ubuntu/Debian**:

```bash
sudo apt update
sudo apt install qemu-system-x86 qemu-utils
```

**Fedora**:

```bash
sudo dnf install qemu-system-x86 qemu-img
```

**Arch Linux**:

```bash
sudo pacman -S qemu-full
```

**Solution 2 - Update Configuration**:

Find correct binary path:

```bash
which qemu-system-x86_64
```

Update your config:

```yaml
binary: /usr/bin/qemu-system-x86_64  # Use correct path
```

### Issue: VM fails with "Could not access KVM kernel module"

**Symptom**: QEMU exits with KVM-related errors.

**Diagnosis**:

```bash
# Check KVM availability
ls -la /dev/kvm

# Check if KVM modules loaded
lsmod | grep kvm

# Check CPU virtualization support
egrep -c '(vmx|svm)' /proc/cpuinfo
# Output > 0 means CPU supports virtualization
```

**Causes**:

1. KVM not enabled in BIOS
2. KVM modules not loaded
3. Permission issue with /dev/kvm
4. CPU doesn't support virtualization

**Solution 1 - Enable Virtualization in BIOS**:

1. Reboot and enter BIOS/UEFI
2. Enable Intel VT-x or AMD-V
3. Save and reboot

**Solution 2 - Load KVM Modules**:

```bash
# For Intel CPUs
sudo modprobe kvm_intel

# For AMD CPUs
sudo modprobe kvm_amd

# Make permanent
echo "kvm_intel" | sudo tee -a /etc/modules
```

**Solution 3 - Fix Permissions**:

```bash
# Check current permissions
ls -la /dev/kvm

# Add user to kvm group
sudo usermod -aG kvm $USER

# Log out and log back in
```

Verify:

```bash
groups | grep kvm
```

**Solution 4 - Disable KVM** (Slower Performance):

Remove KVM from config:

```yaml
arguments:
  - m: "2G"
  - smp: 2
  # Remove: - enable-kvm: null
```

### Issue: VM starts but immediately exits

**Symptom**: VM process starts then terminates within seconds.

**Diagnosis**:

```bash
# Enable debug logging
maqet --log-file /tmp/maqet.log -vv start myvm

# Check log
cat /tmp/maqet.log

# Check VM status
maqet status myvm
```

**Common Causes**:

1. Invalid QEMU arguments
2. Missing required files (BIOS, disk images)
3. Port conflicts
4. Insufficient permissions

**Solution**: Review log file for specific error messages and address accordingly.

### Issue: Configuration errors

**Symptom**: `ERROR: Invalid configuration` or YAML parsing errors.

**Diagnosis**:

```bash
# Validate YAML syntax
python3 -c "import yaml; print(yaml.safe_load(open('config.yaml')))"
```

**Causes**:

1. Invalid YAML syntax
2. Missing required fields
3. Wrong indentation

**Solution**:

**Fix indentation**:

```yaml
# WRONG - tabs or wrong spaces
arguments:
     - m: "2G"

# RIGHT - consistent 2-space indentation
arguments:
  - m: "2G"
```

**Add required fields**:

```yaml
# Minimum valid configuration
binary: /usr/bin/qemu-system-x86_64
arguments:
  - m: "2G"
```

**Quote special characters**:

```yaml
# WRONG - unquoted colons
arguments:
  - netdev: user,hostfwd=tcp::2222-:22

# RIGHT - quoted
arguments:
  - netdev: "user,hostfwd=tcp::2222-:22"
```

---

## Display Issues

### Issue: "Virtio VGA not available" error

**Symptom**: `qemu-system-x86_64: -vga virtio: invalid option`

**Cause**: Your QEMU build doesn't include virtio-vga device support.

**Solution**:

Use standard VGA instead:

```yaml
# BROKEN
arguments:
  - vga: "virtio"

# FIXED
arguments:
  - vga: "std"
```

Standard VGA is universally supported and works well for most use cases.

### Issue: VM starts but no window appears

**Symptom**: VM running but no graphical display.

**Diagnosis**:

```bash
# Check VM status
maqet status myvm

# Check QEMU command line
ps aux | grep qemu | grep myvm
```

**Causes**:

1. No display configured (headless mode)
2. Display explicitly set to "none"
3. VGA set to "none"

**Solution**:

Add display configuration:

```yaml
arguments:
  - display: "gtk"
  - vga: "std"
```

Or use SDL:

```yaml
arguments:
  - display: "sdl"
  - vga: "std"
```

Verify in command line (should see `-display gtk` or similar):

```bash
ps aux | grep qemu | grep myvm
```

### Issue: Display works but screen is blank or garbled

**Symptom**: Window appears but shows nothing or corrupted graphics.

**Causes**:

1. Incompatible VGA device
2. Guest OS boot issues
3. No bootable media

**Solution 1 - Try Different VGA Types**:

```yaml
# Try these in order:
arguments:
  - vga: "std"      # Most compatible
  - vga: "qxl"      # Alternative
  - vga: "cirrus"   # Legacy option
```

**Solution 2 - Check Boot Configuration**:

Ensure you have bootable media:

```yaml
storage:
  - name: hdd
    type: qcow2
    size: 20G

  - name: cdrom
    type: raw
    file: /path/to/bootable.iso
    media: cdrom

arguments:
  - boot: "order=dc"  # Try CD first
```

**Solution 3 - Check BIOS Output**:

The blank screen might be normal if:

- Installing OS from ISO (waiting for installer)
- Booting empty disk (no OS installed)
- Using serial console instead of display

### Issue: "Could not initialize SDL" error

**Symptom**: SDL display fails to start.

**Causes**:

1. X11/Wayland session not available
2. SDL libraries not installed
3. No display server (running over SSH)

**Solution 1 - Use Different Display**:

```yaml
arguments:
  - display: "gtk"  # Instead of sdl
```

**Solution 2 - Install SDL Libraries**:

**Ubuntu/Debian**:

```bash
sudo apt install libsdl2-2.0-0
```

**Solution 3 - Use Headless Mode**:

For remote/SSH sessions:

```yaml
arguments:
  - display: "vnc=:1"  # VNC server
  - vga: "std"
```

Connect with VNC client:

```bash
vncviewer localhost:5901
```

### Issue: "GTK initialization failed" error

**Symptom**: GTK display backend fails.

**Cause**: GTK libraries not available or display server issues.

**Solution 1 - Use Different Display**:

```yaml
arguments:
  - display: "sdl"  # Or vnc
```

**Solution 2 - Check Display Environment**:

```bash
echo $DISPLAY
# Should output something like :0 or :1
```

If empty and you're on X11:

```bash
export DISPLAY=:0
maqet start myvm
```

---

## QMP Connection Issues

### Issue: "QMP socket not found"

**Symptom**: Cannot connect to VM via QMP.

**Diagnosis**:

```bash
# Check runtime directory
ls -la /run/user/$(id -u)/maqet/sockets/

# Check VM status
maqet status myvm
```

**Causes**:

1. VM not running
2. VM started in different process
3. Runtime directory permissions

**Solution 1 - Verify VM Running**:

```bash
maqet ls
# Check if VM status is "running"
```

If stopped:

```bash
maqet start myvm
```

**Solution 2 - Check Process**:

```bash
ps aux | grep qemu | grep myvm
```

If no process, VM crashed. Check logs:

```bash
maqet --log-file /tmp/debug.log -vv start myvm
cat /tmp/debug.log
```

**Solution 3 - Fix Permissions**:

```bash
# Check permissions
ls -la /run/user/$(id -u)/

# Should be owned by your user
# If not, recreate directory:
mkdir -p /run/user/$(id -u)/maqet/sockets
chmod 700 /run/user/$(id -u)/maqet
```

### Issue: "QMP command failed" errors

**Symptom**: QMP commands return errors or timeout.

**Diagnosis**:

```bash
# Try simple query
maqet qmp myvm query-status

# Enable debug output
maqet -vv qmp myvm query-status
```

**Causes**:

1. Invalid QMP command
2. VM not responding
3. QEMU version incompatibility

**Solution 1 - Verify Command**:

Use valid QMP commands:

```bash
# Valid commands
maqet qmp myvm query-status
maqet qmp myvm query-version
maqet qmp keys myvm ctrl alt f2
```

Check QEMU QMP documentation for command names.

**Solution 2 - Restart VM**:

```bash
maqet stop myvm --force
maqet start myvm
```

---

## Storage Issues

### Issue: "Failed to create storage device"

**Symptom**: Storage creation fails during VM add.

**Diagnosis**:

```bash
# Check if directory exists
ls -la ~/.local/share/maqet/storage/

# Check disk space
df -h ~/.local/share/maqet/
```

**Causes**:

1. Insufficient disk space
2. Permission denied
3. Invalid size format
4. qemu-img not found

**Solution 1 - Free Disk Space**:

```bash
# Check available space
df -h

# Clean up old VMs
maqet ls
maqet rm old-vm --force
```

**Solution 2 - Fix Permissions**:

```bash
mkdir -p ~/.local/share/maqet/storage
chmod 755 ~/.local/share/maqet/storage
```

**Solution 3 - Verify qemu-img**:

```bash
which qemu-img

# If not found, install QEMU utilities
sudo apt install qemu-utils  # Ubuntu/Debian
sudo dnf install qemu-img     # Fedora
sudo pacman -S qemu-img       # Arch
```

**Solution 4 - Check Size Format**:

```yaml
# WRONG
storage:
  - name: disk
    size: "20"  # Missing unit

# RIGHT
storage:
  - name: disk
    size: "20G"  # G for gigabytes
```

Valid units: `M` (megabytes), `G` (gigabytes), `T` (terabytes)

### Issue: "Storage file not found"

**Symptom**: VM fails to start, cannot find disk image.

**Diagnosis**:

```bash
# Check configured path
maqet status myvm | grep -A 10 Storage

# Check if file exists
ls -la ~/.local/share/maqet/storage/myvm/
```

**Causes**:

1. Storage file deleted manually
2. Incorrect file path in config
3. File moved or renamed

**Solution 1 - Recreate Storage**:

For qcow2 (will be empty):

```bash
qemu-img create -f qcow2 ~/.local/share/maqet/storage/myvm/disk.qcow2 20G
```

**Solution 2 - Fix Path**:

Update configuration with correct path:

```yaml
storage:
  - name: disk
    type: qcow2
    file: /correct/path/to/disk.qcow2
```

**Solution 3 - Use Existing Disk**:

If you have backup:

```bash
cp /backup/disk.qcow2 ~/.local/share/maqet/storage/myvm/
```

### Issue: Snapshot commands fail

**Symptom**: `ERROR: Snapshots not supported for this device`

**Cause**: Only qcow2 storage supports snapshots.

**Solution**:

Ensure storage type is qcow2:

```yaml
storage:
  - name: disk
    type: qcow2  # Must be qcow2 for snapshots
    size: 20G
```

Raw and VirtFS storage don't support snapshots.

Verify storage type:

```bash
maqet status myvm
# Check Storage Devices section
```

---

## Performance Problems

### Issue: VM is extremely slow

**Symptom**: VM performance much worse than expected.

**Diagnosis**:

```bash
# Check if KVM enabled
ps aux | grep qemu | grep myvm | grep "enable-kvm"

# Check CPU load
top
```

**Causes**:

1. KVM not enabled (no hardware acceleration)
2. Insufficient resources
3. Wrong disk interface
4. Swapping (not enough host RAM)

**Solution 1 - Enable KVM**:

```yaml
arguments:
  - enable-kvm: null
```

Verify KVM works:

```bash
ls -la /dev/kvm
groups | grep kvm
```

Performance difference: 10-50x faster with KVM.

**Solution 2 - Increase Resources**:

```yaml
arguments:
  - m: "4G"      # More memory
  - smp: 4       # More CPU cores
  - cpu: "host"  # Use host CPU features
```

**Solution 3 - Use VirtIO**:

```yaml
storage:
  - name: disk
    interface: virtio  # Much faster than ide/sata

arguments:
  - device: "virtio-net,netdev=net0"  # Faster networking
```

**Solution 4 - Check Host Resources**:

```bash
# Check RAM usage
free -h

# Check CPU usage
top

# Check I/O wait
iostat -x 1
```

Don't over-allocate:

- VM memory < 80% of host memory
- VM CPUs <= host CPUs

### Issue: High CPU usage on host

**Symptom**: QEMU process consuming 100% CPU.

**Causes**:

1. VM doing CPU-intensive work (normal)
2. Busy-wait loop in guest
3. Missing guest drivers

**Solution 1 - Normal Workload**:

If guest is busy, this is expected. Check inside VM:

```bash
# Inside VM
top
```

**Solution 2 - Install Guest Drivers**:

For Linux guests:

```bash
# Ubuntu/Debian
sudo apt install qemu-guest-agent

# Fedora
sudo dnf install qemu-guest-agent
```

**Solution 3 - Limit CPU Usage**:

Reduce CPU cores or use CPU pinning:

```yaml
arguments:
  - smp: 2  # Fewer cores
```

### Issue: Disk I/O is very slow

**Symptom**: File operations inside VM are slow.

**Causes**:

1. Wrong disk interface (ide/sata instead of virtio)
2. qcow2 fragmentation
3. Host I/O bottleneck

**Solution 1 - Use VirtIO**:

```yaml
storage:
  - name: disk
    interface: virtio  # NOT ide or sata
```

**Solution 2 - Convert to Raw** (if space available):

```bash
qemu-img convert -f qcow2 -O raw disk.qcow2 disk.raw
```

Update config:

```yaml
storage:
  - name: disk
    type: raw
    file: /path/to/disk.raw
```

Raw format is faster but takes full space.

**Solution 3 - Check Host Disk**:

```bash
# Check I/O wait
iostat -x 1

# If high I/O wait, host disk is bottleneck
```

---

## Database and State Issues

### Issue: "Database is locked"

**Symptom**: `ERROR: database is locked`

**Cause**: Another MAQET process is accessing the database.

**Solution**:

Wait for other process to finish, or:

```bash
# Check running maqet processes
ps aux | grep maqet

# Kill if stuck
kill <PID>
```

Database location: `~/.local/share/maqet/instances.db`

### Issue: VMs missing from `maqet ls`

**Symptom**: VMs you created don't appear in list.

**Diagnosis**:

```bash
# Check database exists
ls -la ~/.local/share/maqet/instances.db

# Check database content
sqlite3 ~/.local/share/maqet/instances.db "SELECT name, status FROM vm_instances;"
```

**Causes**:

1. Database corrupted
2. Using different data directory
3. VMs removed

**Solution 1 - Check Data Directory**:

```bash
# Default location
ls ~/.local/share/maqet/

# If using custom directory
maqet --data-dir /custom/path ls
```

**Solution 2 - Backup and Recreate** (Last Resort):

```bash
# Backup
cp ~/.local/share/maqet/instances.db ~/.local/share/maqet/instances.db.backup

# Recreate
rm ~/.local/share/maqet/instances.db
maqet ls  # Creates new empty database

# Re-add VMs from configs
maqet add --config vm1.yaml
maqet add --config vm2.yaml
```

### Issue: Stale VM entries (process not running)

**Symptom**: VM shown as "running" but process doesn't exist.

**Diagnosis**:

```bash
# Check VM status
maqet status myvm

# Check process
ps aux | grep <PID>
```

**Cause**: VM process crashed or killed without proper cleanup.

**Solution**:

Force stop to clean up state:

```bash
maqet stop myvm --force
```

MAQET automatically cleans up stale entries on startup (calls `cleanup_dead_processes()`).

---

## Debugging Techniques

### Enable Verbose Logging

```bash
# Level 1: Info + Debug
maqet -v start myvm

# Level 2: More detailed debug
maqet -vv start myvm

# Level 3: Very detailed debug
maqet -vvv start myvm
```

### Save Logs to File

```bash
maqet --log-file /tmp/maqet-debug.log -vv start myvm
cat /tmp/maqet-debug.log
```

File logs always include DEBUG level, regardless of console verbosity.

### Check QEMU Command Line

```bash
# See exact QEMU command used
ps aux | grep qemu | grep myvm

# Format for readability
ps aux | grep qemu | grep myvm | tr ' ' '\n'
```

### Test QEMU Manually

Run QEMU directly to isolate issues:

```bash
/usr/bin/qemu-system-x86_64 \
  -m 2G \
  -enable-kvm \
  -display gtk \
  -vga std \
  -drive file=/path/to/disk.qcow2,if=virtio
```

### Check Database State

```bash
# View all VMs
sqlite3 ~/.local/share/maqet/instances.db "SELECT * FROM vm_instances;"

# View specific VM
sqlite3 ~/.local/share/maqet/instances.db "SELECT * FROM vm_instances WHERE name='myvm';"
```

### Validate Configuration

```bash
# Parse YAML
python3 -c "import yaml; import json; print(json.dumps(yaml.safe_load(open('config.yaml')), indent=2))"
```

### Check System Resources

```bash
# Memory
free -h

# Disk space
df -h

# CPU
lscpu

# Processes
ps aux | grep qemu

# Open files
lsof | grep qemu
```

### Test QMP Manually

```bash
# Install socat
sudo apt install socat  # Ubuntu/Debian

# Connect to QMP socket
socat - UNIX-CONNECT:/run/user/$(id -u)/maqet/sockets/myvm.sock

# In socat prompt, send QMP commands:
{ "execute": "qmp_capabilities" }
{ "execute": "query-status" }
```

### Check QEMU Help

```bash
# List all options
qemu-system-x86_64 -help | less

# List devices
qemu-system-x86_64 -device help

# List VGA options
qemu-system-x86_64 -vga help

# List display options
qemu-system-x86_64 -display help
```

---

## Getting Help

### Before Asking for Help

Gather this information:

1. **MAQET version**: `maqet --version`
2. **Python version**: `python3 --version`
3. **QEMU version**: `qemu-system-x86_64 --version`
4. **Operating System**: `uname -a`
5. **Error message**: Full error output
6. **Configuration**: Your YAML config (remove sensitive data)
7. **Logs**: Output from `maqet -vv <command>`

### Check Documentation

1. [Installation Guide](installation.md)
2. [Quick Start Guide](quickstart.md)
3. [Configuration Guide](configuration.md)
4. [Argument Parsing](../ARGUMENT_PARSING.md)
5. [Project README](../../README.md)

### Search Existing Issues

Before opening new issue:

https://gitlab.com/m4x0n_24/maqet/issues

### Report a Bug

Include:

- Steps to reproduce
- Expected behavior
- Actual behavior
- System information
- Configuration files
- Log output

### Get Community Help

- GitLab Issues: https://gitlab.com/m4x0n_24/maqet/issues
- GitLab Discussions: https://gitlab.com/m4x0n_24/maqet/discussions

---

## Common Error Messages Reference

| Error Message | Cause | Solution |
|--------------|-------|----------|
| `command not found: maqet` | Not in PATH | Add `~/.local/bin` to PATH |
| `ModuleNotFoundError: No module named 'maqet'` | Not installed | `pip install maqet` |
| `QEMU binary not found` | QEMU not installed | Install QEMU package |
| `Could not access KVM` | KVM not enabled | Enable KVM, add user to kvm group |
| `database is locked` | Concurrent access | Wait or kill other process |
| `QMP socket not found` | VM not running | Start VM first |
| `Virtio VGA not available` | QEMU build limitation | Use `-vga std` |
| `Failed to create storage` | Disk space or permissions | Check space and permissions |
| `Invalid configuration` | YAML syntax error | Validate YAML syntax |
| `Could not initialize SDL` | No display server | Use GTK or VNC |

---

## Quick Fixes Checklist

When troubleshooting, try these in order:

1. [ ] Check VM is actually running: `maqet ls`
2. [ ] Check QEMU is installed: `which qemu-system-x86_64`
3. [ ] Enable verbose logging: `maqet -vv <command>`
4. [ ] Validate YAML syntax: `python3 -c "import yaml; yaml.safe_load(open('config.yaml'))"`
5. [ ] Check disk space: `df -h`
6. [ ] Check permissions: `ls -la ~/.local/share/maqet/`
7. [ ] Try minimal config (just binary + memory)
8. [ ] Check QEMU command line: `ps aux | grep qemu`
9. [ ] Test QEMU manually with same arguments
10. [ ] Check logs: `maqet --log-file /tmp/debug.log -vv <command>`

---

**Last Updated**: 2025-10-08
**MAQET Version**: 0.0.10

**Remember**: Most issues have simple solutions. Start with the basics (paths, permissions, resources) before diving into complex debugging.
