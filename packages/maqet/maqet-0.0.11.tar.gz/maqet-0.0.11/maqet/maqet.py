"""
MAQET Core

Main MAQET class implementing unified API for VM management.
All methods are decorated with @api_method to enable automatic CLI
and Python API generation.
"""

import sys
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .api import (
    API_REGISTRY,
    APIRegistry,
    AutoRegisterAPI,
    api_method,
)
from .config import ConfigMerger, ConfigParser
from .constants import Timeouts
from .exceptions import MaqetError, QMPError, SnapshotError, VMLifecycleError
from .generators import CLIGenerator, PythonAPIGenerator
from .logger import LOG
from .machine import Machine
from .managers import QMPManager, SnapshotCoordinator, VMManager
from .snapshot import SnapshotManager
from .state import StateManager, VMInstance
from .storage import StorageManager

# Legacy exception aliases (backward compatibility)
from .exceptions import ConfigError
from .exceptions import QMPManagerError
from .exceptions import SnapshotCoordinatorError
from .exceptions import StateManagerError
from .exceptions import VMManagerError


class Maqet(AutoRegisterAPI):
    """
    MAQET - M4x0n's QEMU Tool

    Unified VM management system that provides CLI commands, Python API,
    and configuration-based
    VM orchestration through a single decorated method interface.

    This class implements your vision of "write once, generate everywhere"
    - each @api_method
    decorated method automatically becomes available as:
    - CLI command (via maqet <command>)
    - Python API method (via maqet.method())
    - Configuration file key (via YAML parsing)

    # TODO(architect, 2025-10-10): [ARCH] CRITICAL - God Object Pattern (1496 lines)
    # Context: This class violates Single Responsibility Principle. It handles:
    # - VM lifecycle (add, start, stop, rm, ls)
    # - QMP operations (qmp, keys, type, screendump, pause, resume, device-add/del)
    # - Storage/snapshots (snapshot create/load/list)
    # - State coordination (StateManager integration)
    # - Config parsing (ConfigParser integration)
    # - CLI/API generation coordination
    # This is Issue #2 in ARCHITECTURAL_REVIEW.md.
    #
    # Impact: Maintainability, testing difficulty, tight coupling, hard to extend
    #
    # Recommendation: Refactor into sub-managers:
    # - VMManager: start, stop, lifecycle
    # - QMPManager: all QMP operations
    # - SnapshotCoordinator: snapshot operations
    # - ConfigManager: configuration handling
    # Maqet becomes facade delegating to managers.
    #
    # Effort: Large (1-2 weeks), but can be done incrementally
    # Priority: Critical for 1.0 release
    # See: ARCHITECTURAL_REVIEW.md Issue #2 for detailed refactoring plan

    # ARCHITECTURAL DESIGN: In-memory Machine Instances
    # ================================================
    # Design Choice: Machine instances stored in memory dict (_machines)
    #   - Simple, fast, no serialization overhead
    #   - Perfect for Python API usage (long-running scripts)
    #   - Trade-off: Lost between CLI invocations
    #
    # Implications:
    #   - CLI Mode: Each command runs in fresh process
    #     * VM state persisted in SQLite (~/.local/share/maqet/instances.db)
    #     * Machine objects recreated on each CLI call
    #     * QMP connections NOT maintained across CLI calls
    #   - Python API Mode: Single process, instances persist
    # * maqet = Maqet(); maqet.start("vm1"); maqet.qmp("vm1", "query-status")
    #     * QMP works seamlessly within same process
    #
    # When to use each mode:
    #   - CLI Mode: Simple VM management (start, stop, status, info, inspect)
    #   - Python API: Automation scripts, CI/CD pipelines, persistent QMP
    #
    # QMP commands work in Python API mode where Machine instances persist
    # across method calls. For CLI workflows requiring QMP, use Python API.
    """

    def __init__(
        self, data_dir: Optional[str] = None, register_signals: bool = True
    ):
        """
        Initialize MAQET instance.

        Args:
            data_dir: Override default XDG data directory
            register_signals: Register signal handlers for graceful shutdown (default: True)
        """
        self.state_manager = StateManager(data_dir)
        self.config_parser = ConfigParser(self)
        self._machines: Dict[str, Machine] = {}
        self._signal_handlers_registered = False

        # Initialize managers
        self.vm_manager = VMManager(self.state_manager, self.config_parser)
        self.qmp_manager = QMPManager(self.state_manager)
        self.snapshot_coordinator = SnapshotCoordinator(self.state_manager)

        # Create instance-specific API registry
        # This allows parallel test execution and multiple Maqet instances
        # with isolated registries (no cross-contamination)
        self._api_registry = APIRegistry()
        self._api_registry.register_from_instance(self)

        if register_signals:
            self._register_signal_handlers()

        # Clean up any stale runner processes via VM manager
        self.vm_manager.cleanup_dead_processes()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        self.cleanup()
        return False  # Don't suppress exceptions

    def _register_signal_handlers(self) -> None:
        """Register signal handlers for graceful shutdown."""
        import signal

        def signal_handler(signum, frame):
            LOG.info(
                f"Received signal {signum}, initiating graceful shutdown..."
            )
            self.cleanup()
            sys.exit(0)

        # Register handlers for SIGINT (Ctrl+C) and SIGTERM
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        self._signal_handlers_registered = True
        LOG.debug("Signal handlers registered for graceful shutdown")

    def get_api_registry(self) -> APIRegistry:
        """
        Get the instance-specific API registry.

        Returns:
            APIRegistry instance for this Maqet instance

        Example:
            maqet = Maqet()
            registry = maqet.get_api_registry()
            methods = registry.get_all_methods()
        """
        return self._api_registry

    def cleanup(self) -> None:
        """Clean up all resources (stop running VMs, close connections).

        Uses ThreadPoolExecutor for parallel VM shutdown to reduce total cleanup time.
        Global timeout of 60 seconds prevents cleanup from blocking indefinitely.
        """
        from concurrent.futures import ThreadPoolExecutor
        from concurrent.futures import TimeoutError as FuturesTimeoutError

        LOG.debug("Cleaning up MAQET resources...")

        # Stop all running VMs
        running_vms = [
            vm_id
            for vm_id, machine in self._machines.items()
            if machine._qemu_machine and machine._qemu_machine.is_running()
        ]

        if running_vms:
            LOG.info(
                f"Stopping {len(running_vms)} running VM(s) in parallel..."
            )

            def stop_vm(vm_id: str) -> tuple[str, bool, str]:
                """Stop a single VM. Returns (vm_id, success, error_msg)."""
                try:
                    LOG.debug(f"Stopping VM {vm_id}")
                    self.stop(vm_id, force=True)
                    return (vm_id, True, "")
                except Exception as e:
                    return (vm_id, False, str(e))

            # Use ThreadPoolExecutor for parallel shutdown
            # Max 10 threads to avoid overwhelming system
            max_workers = min(10, len(running_vms))

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all stop tasks
                futures = {
                    executor.submit(stop_vm, vm_id): vm_id
                    for vm_id in running_vms
                }

                try:
                    # Wait for all tasks with global timeout
                    for future in futures:
                        try:
                            # Per-VM timeout
                            vm_id, success, error = future.result(
                                timeout=Timeouts.CLEANUP_VM_STOP
                            )
                            if not success:
                                LOG.warning(
                                    f"Failed to stop VM {
                                        vm_id} during cleanup: {error}"
                                )
                        except FuturesTimeoutError:
                            vm_id = futures[future]
                            LOG.warning(
                                f"Timeout stopping VM {vm_id} during cleanup"
                            )
                        except Exception as e:
                            vm_id = futures[future]
                            LOG.warning(
                                f"Unexpected error stopping VM {vm_id}: {e}"
                            )

                except Exception as e:
                    LOG.error(f"Error during parallel VM cleanup: {e}")

        # Clear machine cache
        self._machines.clear()
        LOG.debug("MAQET cleanup completed")

    @api_method(
        cli_name="add",
        description="Create a new VM from configuration",
        category="vm",
        examples=[
            "maqet add config.yaml",
            "maqet add config.yaml --name myvm",
            "maqet add --name testvm --memory 4G --cpu 2",
            "maqet add base.yaml custom.yaml --name myvm",
            "maqet add base.yaml --memory 8G",
            "maqet add --name empty-vm --empty",
        ],
    )
    def add(
        self,
        config: Optional[Union[str, List[str]]] = None,
        name: Optional[str] = None,
        empty: bool = False,
        **kwargs,
    ) -> str:
        """
        Create a new VM from configuration file(s) or parameters.

        Delegates to VMManager for actual VM creation logic.

        Args:
            config: Path to YAML configuration file, or list of config
                files for deep-merge
            name: VM name (auto-generated if not provided)
            empty: Create empty VM without any configuration (won't be
                startable until configured)
            **kwargs: Additional VM configuration parameters

        Returns:
            VM instance ID

        Raises:
            MaqetError: If VM creation fails

        Examples:
            Single config: add(config="vm.yaml", name="myvm")
            Multiple configs: add(
                config=["base.yaml", "custom.yaml"], name="myvm"
            )
            Config + params: add(config="base.yaml", memory="8G", cpu=4)
            Empty VM: add(name="placeholder-vm", empty=True)
        """
        try:
            return self.vm_manager.add(config, name, empty, **kwargs)
        except VMManagerError as e:
            raise MaqetError(str(e))

    @api_method(
        cli_name="start",
        description="Start a virtual machine",
        category="vm",
        requires_vm=True,
        examples=["maqet start myvm"],
    )
    def start(self, vm_id: str) -> VMInstance:
        """
        Start a virtual machine by spawning a detached VM runner process.

        Delegates to VMManager for actual VM start logic.

        Args:
            vm_id: VM identifier (name or ID)

        Returns:
            VM instance information

        Raises:
            MaqetError: If VM start fails
        """
        try:
            return self.vm_manager.start(vm_id)
        except VMManagerError as e:
            raise MaqetError(str(e))

    @api_method(
        cli_name="stop",
        description="Stop a virtual machine",
        category="vm",
        requires_vm=True,
        examples=["maqet stop myvm", "maqet stop myvm --force"],
    )
    def stop(
        self, vm_id: str, force: bool = False, timeout: int = Timeouts.VM_STOP
    ) -> VMInstance:
        """
        Stop a VM by sending stop command to VM runner or killing runner process.

        Delegates to VMManager for actual VM stop logic.

        Args:
            vm_id: VM identifier (name or ID)
            force: If True, kill runner immediately (SIGKILL).
                   If False, graceful shutdown (SIGTERM)
            timeout: Timeout for graceful shutdown

        Returns:
            VM instance information

        Raises:
            MaqetError: If VM stop fails
        """
        try:
            return self.vm_manager.stop(vm_id, force, timeout)
        except VMManagerError as e:
            raise MaqetError(str(e))

    @api_method(
        cli_name="rm",
        description="Remove a virtual machine",
        category="vm",
        requires_vm=False,
        examples=[
            "maqet rm myvm",
            "maqet rm myvm --force",
            "maqet rm --all",
            "maqet rm --all --force",
        ],
    )
    def rm(
        self,
        vm_id: Optional[str] = None,
        force: bool = False,
        all: bool = False,
        clean_storage: bool = False,
    ) -> bool:
        """
        Remove a virtual machine completely.

        Delegates to VMManager for actual VM removal logic.

        Args:
            vm_id: VM identifier (name or ID)
            force: Force removal even if VM is running
            all: Remove all virtual machines
            clean_storage: Also delete associated storage files

        Returns:
            True if removed successfully

        Raises:
            MaqetError: If VM removal fails
        """
        try:
            result = self.vm_manager.remove(vm_id, force, all, clean_storage)
            # Clean up machine instances that were removed
            if all:
                self._machines.clear()
            elif vm_id:
                vm = self.state_manager.get_vm(vm_id)
                if vm:
                    self._machines.pop(vm.id, None)
            return result
        except VMManagerError as e:
            raise MaqetError(str(e))

    @api_method(
        cli_name="ls",
        description="List virtual machines in table format",
        category="vm",
        examples=["maqet ls", "maqet ls --status running"],
    )
    def ls(self, status: Optional[str] = None) -> str:
        """
        List virtual machines in readable table format.

        Delegates to VMManager for VM list retrieval.

        Args:
            status: Filter by status ('running', 'stopped', 'created',
                'failed')

        Returns:
            Formatted table string
        """
        vms = self.vm_manager.list_vms(status)

        if not vms:
            return "No virtual machines found."

        # Create table header
        header = f"{'NAME':<20} {'STATUS':<10} {'PID':<8}"
        separator = "-" * 40

        # Build table rows
        rows = [header, separator]
        for vm in vms:
            pid_str = str(vm.pid) if vm.pid else "-"
            row = f"{vm.name:<20} {vm.status:<10} {pid_str:<8}"
            rows.append(row)

        return "\n".join(rows)

    @api_method(
        cli_name="status",
        description="Show comprehensive VM status information",
        category="vm",
        requires_vm=True,
        examples=["maqet status myvm", "maqet status myvm --detailed"],
    )
    def status(self, vm_id: str, detailed: bool = False) -> Dict[str, Any]:
        """
        Get basic status information for a VM.

        Args:
            vm_id: VM identifier (name or ID)
            detailed: (DEPRECATED) Use 'maqet inspect' instead for detailed information

        Returns:
            Dictionary with basic VM status information

        Raises:
            MaqetError: If VM not found
        """
        # Handle deprecated detailed flag
        if detailed:
            LOG.warning(
                "The --detailed flag for 'status' command is deprecated. "
                "Use 'maqet inspect %s' for detailed VM inspection instead.",
                vm_id
            )
            # Redirect to inspect method for backward compatibility
            return self.inspect(vm_id)

        try:
            vm = self.state_manager.get_vm(vm_id)
            if not vm:
                raise MaqetError(f"VM '{vm_id}' not found")

            # Check if process is actually running and update status
            is_actually_running = self._check_process_alive(vm_id, vm)

            # Check if VM is empty/unconfigured
            is_empty_vm = not vm.config_data or not vm.config_data.get(
                "binary"
            )

            # Build simplified status response (no configuration or detailed info)
            status_info = {
                "name": vm.name,
                "status": vm.status,
                "is_running": is_actually_running,
                "is_empty": is_empty_vm,
                "pid": vm.pid,
                "socket_path": vm.socket_path,
            }

            # Add QMP socket info if socket exists
            if vm.socket_path:
                status_info["qmp_socket"] = {
                    "path": vm.socket_path,
                    "exists": os.path.exists(vm.socket_path),
                }

            return status_info

        except Exception as e:
            raise MaqetError(f"Failed to get status for VM '{vm_id}': {e}")

    @api_method(
        cli_name="info",
        description="Show VM configuration details",
        category="vm",
        requires_vm=True,
        examples=["maqet info myvm"],
    )
    def info(self, vm_id: str) -> Dict[str, Any]:
        """
        Get VM configuration details.

        This method provides configuration information about a VM,
        including binary, memory, CPU, display settings, and storage devices.
        It's a focused view of the VM's configuration without runtime details.

        Args:
            vm_id: VM identifier (name or ID)

        Returns:
            Dictionary with VM configuration details

        Raises:
            MaqetError: If VM not found
        """
        try:
            vm = self.state_manager.get_vm(vm_id)
            if not vm:
                raise MaqetError(f"VM '{vm_id}' not found")

            # Build info response with configuration details
            info_data = {
                "vm_id": vm.id,
                "name": vm.name,
                "config_path": vm.config_path,
                "config_data": vm.config_data,
                "configuration": self._get_config_summary(vm.config_data),
            }

            return info_data

        except Exception as e:
            raise MaqetError(f"Failed to get info for VM '{vm_id}': {e}")

    @api_method(
        cli_name="inspect",
        description="Inspect VM with detailed process and resource information",
        category="vm",
        requires_vm=True,
        examples=["maqet inspect myvm"],
    )
    def inspect(self, vm_id: str) -> Dict[str, Any]:
        """
        Get detailed inspection information for a VM.

        This method provides comprehensive information including VM status,
        configuration, process details (if running), QMP socket status,
        and snapshot information. It's the most detailed view of a VM.

        Args:
            vm_id: VM identifier (name or ID)

        Returns:
            Dictionary with comprehensive VM inspection data

        Raises:
            MaqetError: If VM not found
        """
        try:
            vm = self.state_manager.get_vm(vm_id)
            if not vm:
                raise MaqetError(f"VM '{vm_id}' not found")

            # Check if process is actually running
            is_actually_running = self._check_process_alive(vm_id, vm)

            # Build comprehensive inspection response
            inspect_data = {
                "vm_id": vm.id,
                "name": vm.name,
                "status": vm.status,
                "is_running": is_actually_running,
                "pid": vm.pid,
                "socket_path": vm.socket_path,
                "config_path": vm.config_path,
                "created_at": (
                    vm.created_at.isoformat() if vm.created_at else None
                ),
                "updated_at": (
                    vm.updated_at.isoformat() if vm.updated_at else None
                ),
                "configuration": self._get_config_summary(vm.config_data),
            }

            # Add process details if running
            if is_actually_running and vm.pid:
                process_info = self._get_process_info(vm.pid)
                if process_info:
                    inspect_data["process"] = process_info

            # Add QMP socket status
            if vm.socket_path:
                inspect_data["qmp_socket"] = {
                    "path": vm.socket_path,
                    "exists": os.path.exists(vm.socket_path),
                }

            return inspect_data

        except Exception as e:
            raise MaqetError(f"Failed to inspect VM '{vm_id}': {e}")

    def _check_process_alive(self, vm_id: str, vm: VMInstance) -> bool:
        """
        Check if VM process is actually alive and update status if needed.

        Args:
            vm_id: VM identifier
            vm: VM instance

        Returns:
            True if process is alive, False otherwise
        """
        if vm.status != "running" or not vm.pid:
            return False

        try:
            # Send signal 0 to check if process exists
            os.kill(vm.pid, 0)
            return True
        except OSError:
            # Process doesn't exist, update status
            self.state_manager.update_vm_status(
                vm.id, "stopped", pid=None, socket_path=None
            )
            return False

    def _get_config_summary(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract configuration summary from config data.

        Args:
            config_data: VM configuration dictionary

        Returns:
            Dictionary with configuration summary
        """
        summary = {
            "binary": config_data.get("binary"),
            "memory": config_data.get("memory"),
            "cpu": config_data.get("cpu"),
            "display": config_data.get("display"),
        }

        # Count and list storage devices
        storage_devices = config_data.get("storage", [])
        if isinstance(storage_devices, list):
            summary["storage_count"] = len(storage_devices)
            summary["storage_devices"] = [
                {
                    "name": dev.get("name", "unnamed"),
                    "type": dev.get("type", "unknown"),
                    "size": dev.get("size"),
                }
                for dev in storage_devices
            ]
        else:
            summary["storage_count"] = 0
            summary["storage_devices"] = []

        return summary

    def _get_process_info(self, pid: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed process information using psutil if available.

        Args:
            pid: Process ID

        Returns:
            Dictionary with process information or None if psutil not available
        """
        try:
            import psutil

            try:
                proc = psutil.Process(pid)
                return {
                    "cpu_percent": proc.cpu_percent(),
                    "memory_info": proc.memory_info()._asdict(),
                    "create_time": proc.create_time(),
                    "cmdline": proc.cmdline(),
                    "status": proc.status(),
                }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return None
        except ImportError:
            # psutil not available
            return {"note": "Install psutil for detailed process information"}

    @api_method(
        cli_name="qmp",
        description="Execute QMP command on VM",
        category="qmp",
        requires_vm=True,
        hidden=True,
        examples=[
            "maqet qmp myvm system_powerdown",
            "maqet qmp myvm screendump --filename screenshot.ppm",
        ],
    )
    def qmp(self, vm_id: str, command: str, **kwargs) -> Dict[str, Any]:
        """
        Execute QMP command (delegates to QMPManager).

        Args:
            vm_id: VM identifier (name or ID)
            command: QMP command to execute
            **kwargs: Command parameters

        Returns:
            QMP command result

        Raises:
            MaqetError: If VM not found or command fails
        """
        try:
            return self.qmp_manager.execute_qmp(vm_id, command, **kwargs)
        except QMPManagerError as e:
            raise MaqetError(str(e))

    @api_method(
        cli_name="keys",
        description="Send key combination to VM via QMP",
        category="qmp",
        requires_vm=True,
        parent="qmp",
        examples=[
            "maqet qmp keys myvm ctrl alt f2",
            "maqet qmp keys myvm --hold-time 200 ctrl c",
        ],
    )
    def qmp_key(
        self, vm_id: str, *keys: str, hold_time: int = 100
    ) -> Dict[str, Any]:
        """
        Send key combination to VM (delegates to QMPManager).

        Args:
            vm_id: VM identifier (name or ID)
            *keys: Key names to press (e.g., 'ctrl', 'alt', 'f2')
            hold_time: How long to hold keys in milliseconds

        Returns:
            QMP command result

        Raises:
            MaqetError: If VM not found or command fails
        """
        try:
            return self.qmp_manager.send_keys(vm_id, *keys, hold_time=hold_time)
        except QMPManagerError as e:
            raise MaqetError(str(e))

    @api_method(
        cli_name="type",
        description="Type text string to VM via QMP",
        category="qmp",
        requires_vm=True,
        parent="qmp",
        examples=[
            "maqet qmp type myvm 'hello world'",
            "maqet qmp type myvm --hold-time 50 'slow typing'",
        ],
    )
    def qmp_type(
        self, vm_id: str, text: str, hold_time: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Type text string to VM (delegates to QMPManager).

        Args:
            vm_id: VM identifier (name or ID)
            text: Text to type
            hold_time: How long to hold each key in milliseconds

        Returns:
            List of QMP command results

        Raises:
            MaqetError: If VM not found or command fails
        """
        try:
            return self.qmp_manager.type_text(vm_id, text, hold_time=hold_time)
        except QMPManagerError as e:
            raise MaqetError(str(e))

    @api_method(
        cli_name="screendump",
        description="Take screenshot of VM screen",
        category="qmp",
        requires_vm=True,
        parent="qmp",
        examples=[
            "maqet qmp screendump myvm screenshot.ppm",
            "maqet qmp screendump myvm /tmp/vm_screen.ppm",
        ],
    )
    def screendump(self, vm_id: str, filename: str) -> Dict[str, Any]:
        """
        Take screenshot of VM screen (delegates to QMPManager).

        Args:
            vm_id: VM identifier (name or ID)
            filename: Output filename for screenshot

        Returns:
            QMP command result

        Raises:
            MaqetError: If VM not found or command fails
        """
        try:
            return self.qmp_manager.take_screenshot(vm_id, filename)
        except QMPManagerError as e:
            raise MaqetError(str(e))

    @api_method(
        cli_name="pause",
        description="Pause VM execution via QMP",
        category="qmp",
        requires_vm=True,
        parent="qmp",
        examples=["maqet qmp pause myvm"],
    )
    def qmp_stop(self, vm_id: str) -> Dict[str, Any]:
        """
        Pause VM execution via QMP (delegates to QMPManager).

        Args:
            vm_id: VM identifier (name or ID)

        Returns:
            QMP command result

        Raises:
            MaqetError: If VM not found or command fails
        """
        try:
            return self.qmp_manager.pause(vm_id)
        except QMPManagerError as e:
            raise MaqetError(str(e))

    @api_method(
        cli_name="resume",
        description="Resume VM execution via QMP",
        category="qmp",
        requires_vm=True,
        parent="qmp",
        examples=["maqet qmp resume myvm"],
    )
    def qmp_cont(self, vm_id: str) -> Dict[str, Any]:
        """
        Resume VM execution via QMP (delegates to QMPManager).

        Args:
            vm_id: VM identifier (name or ID)

        Returns:
            QMP command result

        Raises:
            MaqetError: If VM not found or command fails
        """
        try:
            return self.qmp_manager.resume(vm_id)
        except QMPManagerError as e:
            raise MaqetError(str(e))

    @api_method(
        cli_name="device-add",
        description="Hot-plug device to VM via QMP",
        category="qmp",
        requires_vm=True,
        parent="qmp",
        examples=[
            "maqet qmp device-add myvm usb-storage --device-id usb1 "
            "--drive usb-drive",
            "maqet qmp device-add myvm e1000 --device-id net1 --netdev user1",
        ],
    )
    def device_add(
        self, vm_id: str, driver: str, device_id: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Hot-plug device to VM via QMP (delegates to QMPManager).

        Args:
            vm_id: VM identifier (name or ID)
            driver: Device driver name (e.g., 'usb-storage', 'e1000')
            device_id: Unique device identifier
            **kwargs: Additional device properties

        Returns:
            QMP command result

        Raises:
            MaqetError: If VM not found or command fails
        """
        try:
            return self.qmp_manager.device_add(vm_id, driver, device_id, **kwargs)
        except QMPManagerError as e:
            raise MaqetError(str(e))

    @api_method(
        cli_name="device-del",
        description="Hot-unplug device from VM via QMP",
        category="qmp",
        requires_vm=True,
        parent="qmp",
        examples=["maqet qmp device-del myvm usb1"],
    )
    def device_del(self, vm_id: str, device_id: str) -> Dict[str, Any]:
        """
        Hot-unplug device from VM via QMP (delegates to QMPManager).

        Args:
            vm_id: VM identifier (name or ID)
            device_id: Device identifier to remove

        Returns:
            QMP command result

        Raises:
            MaqetError: If VM not found or command fails
        """
        try:
            return self.qmp_manager.device_del(vm_id, device_id)
        except QMPManagerError as e:
            raise MaqetError(str(e))

    @api_method(
        cli_name="snapshot",
        description="Manage VM storage snapshots",
        category="storage",
        requires_vm=True,
        examples=[
            "maqet snapshot myvm create ssd backup_name",
            "maqet snapshot myvm load ssd backup_name",
            "maqet snapshot myvm list ssd",
            "maqet snapshot myvm create ssd backup_name --overwrite",
        ],
    )
    def snapshot(
        self,
        vm_id: str,
        action: str,
        drive: str,
        name: Optional[str] = None,
        overwrite: bool = False,
    ) -> Union[Dict[str, Any], List[str]]:
        """
        Manage VM storage snapshots (delegates to SnapshotCoordinator).

        Args:
            vm_id: VM identifier (name or ID)
            action: Snapshot action ('create', 'load', 'list')
            drive: Storage drive name
            name: Snapshot name (required for create/load)
            overwrite: Overwrite existing snapshot (create only)

        Returns:
            Operation result dictionary or list of snapshots

        Raises:
            MaqetError: If VM not found or snapshot operation fails
        """
        try:
            return self.snapshot_coordinator.snapshot(
                vm_id, action, drive, name, overwrite
            )
        except SnapshotCoordinatorError as e:
            raise MaqetError(str(e))
        except SnapshotError as e:
            raise MaqetError(f"Snapshot operation failed: {e}")

    @api_method(
        cli_name="apply",
        description="Apply configuration to existing VM",
        category="vm",
        requires_vm=True,
        examples=[
            "maqet apply myvm config.yaml",
            "maqet apply myvm --memory 8G --cpu 4",
        ],
    )
    def apply(
        self,
        vm_id: str,
        config: Optional[Union[str, List[str]]] = None,
        **kwargs,
    ) -> VMInstance:
        """
        Apply configuration to existing VM, or create it if it doesn't exist.

        Args:
            vm_id: VM identifier (name or ID)
            config: Path to configuration file, or list of config
                files for deep-merge
            **kwargs: Configuration parameters to update

        Returns:
            VM instance (created or updated)

        Raises:
            MaqetError: If configuration is invalid or operation fails
        """
        try:
            # Get VM from database
            vm = self.state_manager.get_vm(vm_id)

            if not vm:
                # VM doesn't exist, create it using add functionality
                LOG.info(f"VM '{vm_id}' not found, creating new VM")
                new_vm_id = self.add(config=config, name=vm_id, **kwargs)
                return self.state_manager.get_vm(new_vm_id)

            # VM exists, update its configuration
            # Load and merge new configuration files
            if config:
                new_config = ConfigMerger.load_and_merge_files(config)
            else:
                new_config = {}

            # Merge kwargs with new config (kwargs take precedence)
            if kwargs:
                new_config = ConfigMerger.deep_merge(new_config, kwargs)

            # Remove name from new_config as it's not QEMU configuration
            # (VM already exists with its name)
            if "name" in new_config:
                new_config = {
                    k: v for k, v in new_config.items() if k != "name"
                }

            # Merge with existing configuration (existing config provides base)
            final_config = ConfigMerger.deep_merge(
                dict(vm.config_data), new_config
            )

            # Validate the merged configuration
            final_config = self.config_parser.validate_config(final_config)

            # Update VM configuration in database
            # This is a simplified approach - in reality we'd update
            # the existing record
            self.state_manager.update_vm_config(vm.id, final_config)

            return self.state_manager.get_vm(vm_id)

        except Exception as e:
            raise MaqetError(
                f"Failed to apply configuration to VM '{vm_id}': {e}"
            )

    def cli(self, args: Optional[List[str]] = None) -> Any:
        """
        Run CLI interface using CLIGenerator.

        Uses instance-specific API registry for isolated command generation.

        Args:
            args: Command line arguments (defaults to sys.argv[1:])

        Returns:
            Result of CLI command execution
        """
        # Use instance-specific registry (falls back to global if not available)
        registry = getattr(self, '_api_registry', API_REGISTRY)
        generator = CLIGenerator(self, registry)
        return generator.run(args)

    def __call__(self, method_name: str, **kwargs) -> Any:
        """
        Direct Python API access.

        Args:
            method_name: Method to execute
            **kwargs: Method parameters

        Returns:
            Method execution result
        """
        generator = PythonAPIGenerator(self, API_REGISTRY)
        return generator.execute_method(method_name, **kwargs)

    def python_api(self):
        """
        Get Python API interface.

        Returns:
            PythonAPIInterface for direct method access
        """
        generator = PythonAPIGenerator(self, API_REGISTRY)
        return generator.generate()


# NOTE: API methods are automatically registered via AutoRegisterAPI
# inheritance
# No manual register_class_methods() call needed!

# NOTE: Line length compliance is now enforced by black formatter
