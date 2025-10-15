# Configuration Guide

Complete reference for configuring MAQET virtual machines.

## Table of Contents

- [Configuration File Format](#configuration-file-format)
- [Required Settings](#required-settings)
- [Optional Settings](#optional-settings)
- [Arguments Configuration](#arguments-configuration)
- [Display and VGA Options](#display-and-vga-options)
- [Storage Configuration](#storage-configuration)
- [Network Configuration](#network-configuration)
- [Configuration Merging](#configuration-merging)
- [Common Templates](#common-templates)
- [Best Practices](#best-practices)

---

## Configuration File Format

MAQET uses YAML files for VM configuration. YAML is human-readable and supports complex nested structures.

### Basic Structure

```yaml
# VM identification
name: vm-name

# QEMU binary path
binary: /usr/bin/qemu-system-x86_64

# QEMU command-line arguments
arguments:
  - key: value
  - flag: null

# Storage devices
storage:
  - name: disk1
    type: qcow2
    size: 20G

# Optional: Logging
log_file: /tmp/vm.log
```

### YAML Syntax Notes

- **Indentation**: Use 2 spaces (not tabs)
- **Lists**: Start with `-` (dash + space)
- **Comments**: Start with `#`
- **Strings**: Quote if contains special characters (`:`, `,`, `=`)
- **Null values**: Use `null` or `~`

---

## Required Settings

### binary

**Type**: String
**Required**: Yes
**Description**: Path to QEMU system binary

**Examples**:

```yaml
binary: /usr/bin/qemu-system-x86_64
```

```yaml
binary: /usr/bin/qemu-system-aarch64
```

Find your QEMU binary:

```bash
which qemu-system-x86_64
```

Common paths:

- Ubuntu/Debian: `/usr/bin/qemu-system-x86_64`
- Fedora: `/usr/bin/qemu-system-x86_64`
- Arch Linux: `/usr/bin/qemu-system-x86_64`
- Custom builds: `/usr/local/bin/qemu-system-x86_64`

---

## Optional Settings

### name

**Type**: String
**Required**: No (can be specified via CLI: `maqet add --name myvm`)
**Description**: Unique identifier for the VM

**Example**:

```yaml
name: ubuntu-dev-vm
```

**Best Practices**:

- Use descriptive names: `ubuntu-22-webserver` not `vm1`
- Use hyphens or underscores, avoid spaces
- Keep names short but meaningful

### memory

**Type**: String
**Description**: RAM allocation (alternative to `arguments: [{m: value}]`)

**Examples**:

```yaml
memory: 2G      # 2 gigabytes
memory: 4096M   # 4096 megabytes
memory: 512M    # 512 megabytes
```

**Equivalent to**:

```yaml
arguments:
  - m: "2G"
```

### cpu

**Type**: Integer
**Description**: Number of CPU cores (alternative to `arguments: [{smp: value}]`)

**Examples**:

```yaml
cpu: 2    # 2 cores
cpu: 4    # 4 cores
cpu: 8    # 8 cores
```

**Equivalent to**:

```yaml
arguments:
  - smp: 2
```

### display

**Type**: String
**Description**: Display backend type

**Examples**:

```yaml
display: gtk     # GTK graphical window
display: sdl     # SDL graphical window
display: vnc     # VNC server
display: none    # Headless mode
```

See [Display and VGA Options](#display-and-vga-options) for details.

### vga

**Type**: String
**Description**: VGA device type

**Examples**:

```yaml
vga: std      # Standard VGA (recommended)
vga: virtio   # VirtIO GPU (requires guest drivers)
vga: qxl      # QXL paravirtual (for SPICE)
vga: none     # No VGA device
```

See [Display and VGA Options](#display-and-vga-options) for details.

### log_file

**Type**: String
**Description**: Path to log file for VM output

**Example**:

```yaml
log_file: /tmp/my-vm.log
```

Or use CLI option:

```bash
maqet --log-file /tmp/my-vm.log start my-vm
```

---

## Arguments Configuration

The `arguments` key allows you to specify any QEMU command-line argument in YAML format.

### Argument Formats

MAQET supports three argument formats:

#### 1. Dictionary Format: {key: value}

For arguments with values:

```yaml
arguments:
  - m: "2G"              # -m 2G
  - smp: 4               # -smp 4
  - cpu: "host"          # -cpu host
  - display: "gtk"       # -display gtk
```

#### 2. Flag Format: {key: null}

For boolean flags without values:

```yaml
arguments:
  - enable-kvm: null     # -enable-kvm
  - no-reboot: null      # -no-reboot
  - no-shutdown: null    # -no-shutdown
```

#### 3. String Format: "key"

Alternative flag syntax:

```yaml
arguments:
  - "enable-kvm"         # -enable-kvm
  - "snapshot"           # -snapshot
```

### Mixed Format Example

```yaml
arguments:
  # Memory and CPU
  - m: "4G"
  - smp: 2
  - cpu: "host"

  # Acceleration
  - enable-kvm: null

  # Display
  - display: "gtk"
  - vga: "std"

  # Boot options
  - "no-reboot"
```

### Complex Arguments (Comma-Separated)

For QEMU arguments with suboptions:

```yaml
arguments:
  # Network with port forwarding
  - netdev: "user,id=net0,hostfwd=tcp::2222-:22"
  - device: "virtio-net,netdev=net0"

  # Display with options
  - display: "gtk,zoom-to-fit=on,show-menubar=off"

  # Boot order
  - boot: "order=dc,menu=on"
```

### Nested Dictionary Format

For complex arguments with multiple suboptions:

```yaml
arguments:
  - device:
      driver: "virtio-net"
      netdev: "net0"
      mac: "52:54:00:12:34:56"
```

**Generates**: `-device driver=virtio-net,netdev=net0,mac=52:54:00:12:34:56`

**Note**: Some QEMU arguments expect positional values (e.g., `-display gtk` not `-display type=gtk`). For these, use the comma-separated string format.

See [ARGUMENT_PARSING.md](../ARGUMENT_PARSING.md) for complete documentation.

---

## Display and VGA Options

### Display Types

#### GTK (Graphical Window)

```yaml
arguments:
  - display: "gtk"
  - vga: "std"
```

**Features**:

- Native GTK+ window
- Good performance
- Zoom and fullscreen support

**Options**:

```yaml
arguments:
  - display: "gtk,zoom-to-fit=on,show-menubar=off"
```

#### SDL (Simple DirectMedia Layer)

```yaml
arguments:
  - display: "sdl"
  - vga: "std"
```

**Features**:

- Cross-platform
- Good gaming performance
- Fullscreen support

#### VNC (Remote Desktop)

```yaml
arguments:
  - display: "vnc=:1"
  - vga: "std"
```

**Features**:

- Remote access via VNC client
- No local graphical output
- Connect: `vncviewer localhost:5901`

#### Headless (No Display)

```yaml
arguments:
  - display: "none"
```

**Features**:

- No graphical output
- Minimal resource usage
- VGA automatically set to `none`
- Access via serial console or SSH

### VGA Device Types

#### std (Standard VGA)

```yaml
arguments:
  - vga: "std"
```

**Best for**:

- Maximum compatibility
- All QEMU builds support it
- Desktop operating systems

**Recommended**: Use this unless you have specific needs.

#### virtio (VirtIO GPU)

```yaml
arguments:
  - vga: "virtio"
```

**Best for**:

- Modern Linux guests with VirtIO drivers
- Better performance than std
- 3D acceleration support

**Requirements**:

- Guest OS with VirtIO drivers
- QEMU build with VirtIO support

**Note**: Not all QEMU builds include virtio-vga. If you get "VGA not available" error, use `std`.

#### qxl (QXL Paravirtual)

```yaml
arguments:
  - vga: "qxl"
```

**Best for**:

- SPICE protocol
- Remote desktop scenarios
- Windows guests

#### cirrus (Cirrus Logic)

```yaml
arguments:
  - vga: "cirrus"
```

**Status**: Deprecated, use `std` instead

#### none (No VGA)

```yaml
arguments:
  - vga: "none"
```

**Best for**:

- Headless servers
- Serial console only
- Minimal resource usage

### Display Configuration Examples

**Desktop VM with Window**:

```yaml
arguments:
  - display: "gtk,zoom-to-fit=on"
  - vga: "std"
```

**Headless Server**:

```yaml
arguments:
  - display: "none"
  # No vga setting needed (automatically set to none)
```

**Remote Access via VNC**:

```yaml
arguments:
  - display: "vnc=0.0.0.0:1"  # Listen on all interfaces
  - vga: "std"
```

Connect from remote machine:

```bash
vncviewer <server-ip>:5901
```

### Display Behavior

MAQET provides smart defaults:

- **No display configured**: Headless mode (`-vga none`)
- **display=gtk/sdl**: Graphical mode (QEMU chooses VGA)
- **display=none**: Headless mode (`-vga none`)
- **Explicit vga setting**: Always honored

**Override defaults explicitly**:

```yaml
arguments:
  - display: "gtk"
  - vga: "virtio"  # Override default std
```

---

## Storage Configuration

Storage devices are defined in the `storage` list.

### QCOW2 Storage (Copy-On-Write)

```yaml
storage:
  - name: hdd
    type: qcow2
    size: 20G
    interface: virtio
```

**Options**:

- **name** (required): Device identifier
- **type**: `qcow2`
- **size** (required): Disk size (e.g., `20G`, `500M`, `1T`)
- **file** (optional): Path to disk image (auto-generated if omitted)
- **interface**: `virtio`, `sata`, `ide`, `scsi` (default: `virtio`)
- **media**: `disk` (default), `cdrom`

**Features**:

- Thin provisioning (only uses space as needed)
- Snapshot support
- Compression support

**Auto-creation**: MAQET automatically creates missing qcow2 files.

### Raw Storage

```yaml
storage:
  - name: cdrom
    type: raw
    file: /path/to/ubuntu.iso
    interface: sata
    media: cdrom
```

**Options**:

- **name** (required): Device identifier
- **type**: `raw`
- **file** (required): Path to ISO or raw disk image
- **interface**: `virtio`, `sata`, `ide`, `scsi`
- **media**: `disk`, `cdrom`

**Use cases**:

- Boot ISOs
- Pre-built disk images
- Physical device passthrough

### VirtFS (Shared Folders)

```yaml
storage:
  - name: shared
    type: virtfs
    path: /home/user/projects
    mount_tag: hostshare
    security_model: mapped-xattr
    readonly: false
```

**Options**:

- **name** (required): Device identifier
- **type**: `virtfs`
- **path** (required): Host directory to share
- **mount_tag** (required): Tag used for mounting in guest
- **security_model**: `none`, `passthrough`, `mapped`, `mapped-xattr` (default: `mapped-xattr`)
- **readonly**: `true`, `false` (default: `false`)

**Guest mounting (Linux)**:

```bash
sudo mount -t 9p -o trans=virtio hostshare /mnt/shared
```

**Security Models**:

- **none**: No security mapping (fastest, least secure)
- **passthrough**: Direct UID/GID mapping (requires root)
- **mapped**: Map permissions to extended attributes (recommended)
- **mapped-xattr**: Same as mapped with better performance

### Storage Examples

**System disk + Installation ISO**:

```yaml
storage:
  - name: system
    type: qcow2
    size: 50G
    interface: virtio

  - name: install
    type: raw
    file: /path/to/ubuntu-22.04.iso
    interface: sata
    media: cdrom
```

**Multiple disks**:

```yaml
storage:
  - name: system
    type: qcow2
    size: 30G
    interface: virtio

  - name: data
    type: qcow2
    size: 100G
    interface: virtio

  - name: backup
    type: qcow2
    size: 200G
    interface: virtio
```

**Shared development environment**:

```yaml
storage:
  - name: system
    type: qcow2
    size: 20G
    interface: virtio

  - name: projects
    type: virtfs
    path: /home/user/dev/projects
    mount_tag: projects
    security_model: mapped-xattr
```

---

## Network Configuration

Network configuration is done via QEMU arguments.

### User Mode Networking (NAT)

Simplest network setup, no root required:

```yaml
arguments:
  - netdev: "user,id=net0"
  - device: "virtio-net,netdev=net0"
```

**Features**:

- NAT (guest can access internet)
- No incoming connections
- No configuration needed

### User Mode with Port Forwarding

Forward host ports to guest:

```yaml
arguments:
  - netdev: "user,id=net0,hostfwd=tcp::2222-:22"
  - device: "virtio-net,netdev=net0"
```

This forwards host port 2222 to guest port 22 (SSH).

Connect from host:

```bash
ssh -p 2222 user@localhost
```

**Multiple port forwards**:

```yaml
arguments:
  - netdev: "user,id=net0,hostfwd=tcp::2222-:22,hostfwd=tcp::8080-:80"
  - device: "virtio-net,netdev=net0"
```

### Bridge Mode Networking

Connect VM to host network bridge (requires root):

```yaml
arguments:
  - netdev: "bridge,id=net0,br=virbr0"
  - device: "virtio-net,netdev=net0"
```

**Requirements**:

- Bridge interface configured on host
- QEMU helper with setuid (qemu-bridge-helper)

### TAP Interface

Direct TAP device (requires root):

```yaml
arguments:
  - netdev: "tap,id=net0,ifname=tap0,script=no,downscript=no"
  - device: "virtio-net,netdev=net0"
```

### Custom MAC Address

Set specific MAC address:

```yaml
arguments:
  - netdev: "user,id=net0"
  - device: "virtio-net,netdev=net0,mac=52:54:00:12:34:56"
```

---

## Configuration Merging

MAQET supports merging multiple configuration files using deep-merge semantics.

### Basic Merging

```bash
maqet add --config base.yaml --config overrides.yaml
```

**base.yaml**:

```yaml
binary: /usr/bin/qemu-system-x86_64
arguments:
  - m: "2G"
  - smp: 2
```

**overrides.yaml**:

```yaml
arguments:
  - m: "4G"    # Override memory
  - display: "gtk"  # Add display
```

**Result**:

```yaml
binary: /usr/bin/qemu-system-x86_64
arguments:
  - m: "4G"        # Overridden
  - smp: 2         # From base
  - display: "gtk" # Added
```

### List Concatenation

Lists are concatenated, not replaced:

**base.yaml**:

```yaml
storage:
  - name: hdd
    type: qcow2
    size: 20G
```

**overrides.yaml**:

```yaml
storage:
  - name: cdrom
    type: raw
    file: /path/to/iso
```

**Result**:

```yaml
storage:
  - name: hdd
    type: qcow2
    size: 20G
  - name: cdrom
    type: raw
    file: /path/to/iso
```

### Override Priority

Later configs override earlier ones:

```bash
maqet add --config base.yaml --config override1.yaml --config override2.yaml
```

Priority: `override2.yaml` > `override1.yaml` > `base.yaml`

### CLI Arguments Override Config

Command-line arguments have highest priority:

```bash
maqet add --config vm.yaml --memory 8G --cpu 4
```

This overrides `memory` and `cpu` from `vm.yaml`.

---

## Common Templates

### Desktop VM Template

```yaml
name: desktop-vm
binary: /usr/bin/qemu-system-x86_64

arguments:
  - m: "4G"
  - smp: 4
  - cpu: "host"
  - enable-kvm: null
  - display: "gtk,zoom-to-fit=on"
  - vga: "std"
  - device: "usb-tablet"  # Better mouse handling

storage:
  - name: system
    type: qcow2
    size: 50G
    interface: virtio
```

### Server VM Template

```yaml
name: server-vm
binary: /usr/bin/qemu-system-x86_64

arguments:
  - m: "8G"
  - smp: 4
  - cpu: "host"
  - enable-kvm: null
  - display: "none"
  - netdev: "user,id=net0,hostfwd=tcp::2222-:22"
  - device: "virtio-net,netdev=net0"

storage:
  - name: system
    type: qcow2
    size: 50G
    interface: virtio

  - name: data
    type: qcow2
    size: 100G
    interface: virtio
```

### Minimal Test VM Template

```yaml
name: test-vm
binary: /usr/bin/qemu-system-x86_64

arguments:
  - m: "512M"
  - smp: 1
  - enable-kvm: null
  - display: "none"

storage:
  - name: disk
    type: qcow2
    size: 5G
    interface: virtio
```

### Development VM with Shared Folders

```yaml
name: dev-vm
binary: /usr/bin/qemu-system-x86_64

arguments:
  - m: "4G"
  - smp: 2
  - cpu: "host"
  - enable-kvm: null
  - display: "gtk"
  - vga: "std"
  - netdev: "user,id=net0,hostfwd=tcp::2222-:22"
  - device: "virtio-net,netdev=net0"

storage:
  - name: system
    type: qcow2
    size: 30G
    interface: virtio

  - name: projects
    type: virtfs
    path: /home/user/projects
    mount_tag: projects
    security_model: mapped-xattr

  - name: documents
    type: virtfs
    path: /home/user/documents
    mount_tag: documents
    security_model: mapped-xattr
    readonly: true
```

### High-Performance VM Template

```yaml
name: performance-vm
binary: /usr/bin/qemu-system-x86_64

arguments:
  - m: "16G"
  - smp: "8,cores=4,threads=2,sockets=1"
  - cpu: "host,+x2apic,+tsc-deadline"
  - enable-kvm: null
  - machine: "q35,accel=kvm"
  - display: "none"

storage:
  - name: system
    type: qcow2
    size: 100G
    interface: virtio
```

---

## Best Practices

### 1. Use Descriptive Names

```yaml
# Good
name: ubuntu-22-webserver

# Avoid
name: vm1
```

### 2. Always Enable KVM

```yaml
arguments:
  - enable-kvm: null
```

Verify KVM is available:

```bash
ls -la /dev/kvm
```

### 3. Use VirtIO Devices

```yaml
storage:
  - name: disk
    interface: virtio  # Much faster than ide/sata
```

```yaml
arguments:
  - device: "virtio-net,netdev=net0"  # Faster than e1000
```

### 4. Allocate Appropriate Resources

**Desktop VM**:

- Memory: 4-8GB
- CPU: 2-4 cores
- Disk: 30-50GB

**Server VM**:

- Memory: 2-16GB (depends on workload)
- CPU: 2-8 cores
- Disk: 20GB+ (depends on data)

**Test VM**:

- Memory: 512M-2GB
- CPU: 1-2 cores
- Disk: 5-10GB

### 5. Organize Configuration Files

```
~/vms/
├── templates/
│   ├── base.yaml          # Common settings
│   ├── desktop.yaml       # Desktop defaults
│   └── server.yaml        # Server defaults
└── instances/
    ├── web-server.yaml
    ├── database.yaml
    └── dev-env.yaml
```

Use merging:

```bash
maqet add --config templates/base.yaml --config templates/server.yaml --config instances/web-server.yaml
```

### 6. Quote Special Characters

```yaml
arguments:
  - append: "root=/dev/vda1 console=ttyS0"  # Quoted
  - netdev: "user,id=net0,hostfwd=tcp::2222-:22"  # Quoted
```

### 7. Use Comments

```yaml
arguments:
  # Memory and CPU configuration
  - m: "4G"         # 4GB RAM
  - smp: 4          # 4 CPU cores
  - cpu: "host"     # Use host CPU features

  # Acceleration
  - enable-kvm: null  # Enable KVM for performance

  # Display configuration
  - display: "gtk"    # GTK graphical window
  - vga: "std"        # Standard VGA (most compatible)
```

### 8. Validate YAML Syntax

Before using a config:

```bash
python3 -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

No output = valid YAML.

### 9. Test Incrementally

Start with minimal config, add features one at a time:

1. Basic VM (CPU, memory, disk)
2. Add display
3. Add network
4. Add advanced features

### 10. Keep Configs in Version Control

```bash
cd ~/vms
git init
git add *.yaml
git commit -m "Initial VM configurations"
```

---

## Configuration Validation

MAQET validates configurations when loading. Common errors:

### Missing Required Fields

```
ERROR: Configuration missing required field 'binary'
```

**Fix**: Add `binary: /path/to/qemu` to config.

### Invalid YAML Syntax

```
ERROR: Failed to parse YAML: mapping values are not allowed here
```

**Fix**: Check indentation and quote strings with special characters.

### Unknown Configuration Keys

```
WARNING: Unknown configuration key 'memory_size' (did you mean 'memory'?)
```

**Fix**: Use correct key names (see this guide for valid keys).

### Invalid Argument Format

```
ERROR: Invalid argument format in arguments list
```

**Fix**: Use correct argument format (dict, flag, or string).

---

## Advanced Configuration

### UEFI Boot

```yaml
arguments:
  - bios: "/usr/share/ovmf/OVMF.fd"
```

Or for UEFI with variables:

```yaml
arguments:
  - drive: "if=pflash,format=raw,readonly=on,file=/usr/share/ovmf/OVMF_CODE.fd"
  - drive: "if=pflash,format=raw,file=/path/to/OVMF_VARS.fd"
```

### Custom Boot Order

```yaml
arguments:
  - boot: "order=dc,menu=on"  # Try CD first, then disk, show boot menu
```

### Sound Card

```yaml
arguments:
  - device: "intel-hda"
  - device: "hda-duplex"
```

### USB Passthrough

```yaml
arguments:
  - device: "usb-host,vendorid=0x1234,productid=0x5678"
```

Find USB device IDs:

```bash
lsusb
```

### NUMA Configuration

```yaml
arguments:
  - numa: "node,nodeid=0,cpus=0-3,mem=8G"
  - numa: "node,nodeid=1,cpus=4-7,mem=8G"
```

---

## Next Steps

- **[Quick Start Guide](quickstart.md)**: Create your first VM
- **[Argument Parsing](../ARGUMENT_PARSING.md)**: Advanced YAML syntax
- **[Troubleshooting](troubleshooting.md)**: Common issues and solutions

---

**Last Updated**: 2025-10-08
**MAQET Version**: 0.0.10
