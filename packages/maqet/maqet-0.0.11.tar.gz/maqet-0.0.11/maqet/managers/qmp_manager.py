"""
QMP Manager

Manages QMP (QEMU Machine Protocol) operations for VMs.
All QMP commands are sent via IPC to VM runner processes.

Responsibilities:
- Execute arbitrary QMP commands
- Send keyboard input (keys, typing)
- Take screenshots
- Pause/resume VM execution
- Hot-plug/unplug devices
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from ..constants import QMP as QPMConstants
from ..constants import Timeouts
from ..exceptions import (
    IPCError,
    QMPCommandError,
    QMPError,
    VMNotFoundError,
    VMNotRunningError,
)
from ..ipc.runner_client import RunnerClient
from ..logger import LOG
from ..qmp import KeyboardEmulator
from ..state import StateManager, VMInstance

# Legacy exception aliases (backward compatibility)
QMPManagerError = QMPError
RunnerClientError = IPCError


class QMPManager:
    """
    Manages QMP (QEMU Machine Protocol) operations.

    All QMP commands are sent to VM runner processes via IPC (Inter-Process
    Communication). The VM runner handles QMP interaction with QEMU.

    This enables QMP to work regardless of whether the VM was started from
    CLI or Python API, fixing the previous limitation where QMP only worked
    in Python API mode.
    """

    def __init__(self, state_manager: StateManager):
        """
        Initialize QMP manager.

        Args:
            state_manager: State management instance for VM database access
        """
        self.state_manager = state_manager
        LOG.debug("QMPManager initialized")

    def execute_qmp(self, vm_id: str, command: str, **kwargs) -> Dict[str, Any]:
        """
        Execute arbitrary QMP command on VM via IPC.

        Args:
            vm_id: VM identifier (name or ID)
            command: QMP command to execute (e.g., "query-status", "system_powerdown")
            **kwargs: Command parameters

        Returns:
            QMP command result dictionary

        Raises:
            QMPManagerError: If VM not found, not running, or command fails

        Example:
            result = qmp_manager.execute_qmp("myvm", "query-status")
            result = qmp_manager.execute_qmp("myvm", "screendump", filename="screen.ppm")
        """
        try:
            # Get VM from database
            vm = self.state_manager.get_vm(vm_id)
            if not vm:
                raise QMPManagerError(f"VM '{vm_id}' not found")

            # Check VM is running
            if vm.status != "running":
                raise QMPManagerError(
                    f"VM '{vm_id}' is not running (status: {vm.status})"
                )

            # Verify runner process is alive
            if not vm.runner_pid:
                raise QMPManagerError(
                    f"VM '{vm_id}' has no runner process (state corrupted)"
                )

            # Create IPC client and send QMP command
            client = RunnerClient(vm.id, self.state_manager)

            try:
                result = client.send_command("qmp", command, **kwargs)
                LOG.debug(f"QMP command '{command}' executed successfully on {vm_id}")
                return result

            except RunnerClientError as e:
                raise QMPManagerError(f"Failed to communicate with VM runner: {e}")

        except QMPManagerError:
            raise
        except Exception as e:
            raise QMPManagerError(f"QMP command failed on VM '{vm_id}': {e}")

    def send_keys(
        self, vm_id: str, *keys: str, hold_time: int = 100
    ) -> Dict[str, Any]:
        """
        Send key combination to VM via QMP.

        Uses KeyboardEmulator to translate key names into QMP send-key command.

        Args:
            vm_id: VM identifier (name or ID)
            *keys: Key names to press (e.g., 'ctrl', 'alt', 'f2')
            hold_time: How long to hold keys in milliseconds (default: 100)

        Returns:
            QMP command result dictionary

        Raises:
            QMPManagerError: If VM not found, not running, or command fails

        Example:
            qmp_manager.send_keys("myvm", "ctrl", "alt", "f2")
            qmp_manager.send_keys("myvm", "ret", hold_time=200)
        """
        try:
            # Generate QMP command from key names
            qmp_cmd = KeyboardEmulator.press_keys(*keys, hold_time=hold_time)

            # Execute QMP command via IPC
            result = self.execute_qmp(
                vm_id, qmp_cmd["command"], **qmp_cmd["arguments"]
            )

            LOG.debug(f"Sent keys {keys} to VM {vm_id}")
            return result

        except Exception as e:
            raise QMPManagerError(f"Failed to send keys to VM '{vm_id}': {e}")

    def type_text(
        self, vm_id: str, text: str, hold_time: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Type text string to VM via QMP.

        Sends each character as a separate QMP send-key command.

        Args:
            vm_id: VM identifier (name or ID)
            text: Text to type
            hold_time: How long to hold each key in milliseconds (default: 100)

        Returns:
            List of QMP command results (one per character)

        Raises:
            QMPManagerError: If VM not found, not running, or command fails

        Example:
            qmp_manager.type_text("myvm", "hello world")
            qmp_manager.type_text("myvm", "slow typing", hold_time=50)
        """
        try:
            # Generate QMP commands for each character
            qmp_commands = KeyboardEmulator.type_string(text, hold_time=hold_time)

            # Execute each command via IPC
            results = []
            for cmd in qmp_commands:
                result = self.execute_qmp(
                    vm_id, cmd["command"], **cmd["arguments"]
                )
                results.append(result)

            LOG.debug(f"Typed {len(text)} characters to VM {vm_id}")
            return results

        except Exception as e:
            raise QMPManagerError(f"Failed to type text to VM '{vm_id}': {e}")

    def take_screenshot(self, vm_id: str, filename: str) -> Dict[str, Any]:
        """
        Take screenshot of VM screen.

        Saves screenshot to specified file in PPM format (QEMU default).

        Args:
            vm_id: VM identifier (name or ID)
            filename: Output filename for screenshot (e.g., "screenshot.ppm")

        Returns:
            QMP command result dictionary

        Raises:
            QMPManagerError: If VM not found, not running, or command fails

        Example:
            qmp_manager.take_screenshot("myvm", "/tmp/screenshot.ppm")
        """
        try:
            result = self.execute_qmp(vm_id, "screendump", filename=filename)
            LOG.info(f"Screenshot saved to {filename} for VM {vm_id}")
            return result

        except Exception as e:
            raise QMPManagerError(
                f"Failed to take screenshot of VM '{vm_id}': {e}"
            )

    def pause(self, vm_id: str) -> Dict[str, Any]:
        """
        Pause VM execution via QMP.

        Suspends VM execution (freezes guest). VM can be resumed later.

        Args:
            vm_id: VM identifier (name or ID)

        Returns:
            QMP command result dictionary

        Raises:
            QMPManagerError: If VM not found, not running, or command fails

        Example:
            qmp_manager.pause("myvm")
        """
        try:
            result = self.execute_qmp(vm_id, "stop")
            LOG.info(f"VM {vm_id} paused")
            return result

        except Exception as e:
            raise QMPManagerError(f"Failed to pause VM '{vm_id}': {e}")

    def resume(self, vm_id: str) -> Dict[str, Any]:
        """
        Resume VM execution via QMP.

        Resumes a previously paused VM.

        Args:
            vm_id: VM identifier (name or ID)

        Returns:
            QMP command result dictionary

        Raises:
            QMPManagerError: If VM not found, not running, or command fails

        Example:
            qmp_manager.resume("myvm")
        """
        try:
            result = self.execute_qmp(vm_id, "cont")
            LOG.info(f"VM {vm_id} resumed")
            return result

        except Exception as e:
            raise QMPManagerError(f"Failed to resume VM '{vm_id}': {e}")

    def device_add(
        self, vm_id: str, driver: str, device_id: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Hot-plug device to VM via QMP.

        Adds a device to running VM without restart.

        Args:
            vm_id: VM identifier (name or ID)
            driver: Device driver name (e.g., 'usb-storage', 'e1000', 'virtio-net-pci')
            device_id: Unique device identifier
            **kwargs: Additional device properties (e.g., drive="usb-drive", netdev="user1")

        Returns:
            QMP command result dictionary

        Raises:
            QMPManagerError: If VM not found, not running, or command fails

        Example:
            qmp_manager.device_add("myvm", "usb-storage", "usb1", drive="usb-drive")
            qmp_manager.device_add("myvm", "e1000", "net1", netdev="user1")
        """
        try:
            result = self.execute_qmp(
                vm_id, "device_add", driver=driver, id=device_id, **kwargs
            )
            LOG.info(f"Device {device_id} (driver={driver}) added to VM {vm_id}")
            return result

        except Exception as e:
            raise QMPManagerError(f"Failed to add device to VM '{vm_id}': {e}")

    def device_del(self, vm_id: str, device_id: str) -> Dict[str, Any]:
        """
        Hot-unplug device from VM via QMP.

        Removes a device from running VM without restart.

        Args:
            vm_id: VM identifier (name or ID)
            device_id: Device identifier to remove

        Returns:
            QMP command result dictionary

        Raises:
            QMPManagerError: If VM not found, not running, or command fails

        Example:
            qmp_manager.device_del("myvm", "usb1")
        """
        try:
            result = self.execute_qmp(vm_id, "device_del", id=device_id)
            LOG.info(f"Device {device_id} removed from VM {vm_id}")
            return result

        except Exception as e:
            raise QMPManagerError(
                f"Failed to remove device from VM '{vm_id}': {e}"
            )
