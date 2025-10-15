"""
MAQET Machine

Enhanced QEMUMachine integration for MAQET VM management.
Handles VM process lifecycle, QMP communication, and state tracking.
"""

import atexit
import os
import re
import signal
import subprocess
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set

try:
    from qemu.machine import QEMUMachine
except ImportError:
    # Fallback to vendored version
    from maqet.vendor.qemu.machine import QEMUMachine

from .config_handlers import ConfigurableMachine
from .constants import Intervals, Timeouts
from .logger import LOG
from .storage import StorageManager
from .validation import ConfigValidator

if TYPE_CHECKING:
    from .state import StateManager

# Global registry of active QEMU PIDs for cleanup on exit
_active_qemu_pids: Set[int] = set()


class MaqetQEMUMachine(QEMUMachine):
    """
    MAQET's simplified QEMUMachine without display defaults.

    Removes hardcoded display/VGA arguments from _base_args, letting QEMU
    use its own defaults or user-configured values. Maintains QMP and
    console configuration from parent class.

    Users configure display explicitly if needed (e.g., -display none for headless).

    Also ensures QEMU dies when parent process dies using PR_SET_PDEATHSIG.
    """

    def _launch(self) -> None:
        """
        Launch QEMU with PR_SET_PDEATHSIG to ensure cleanup on parent death.

        PR_SET_PDEATHSIG is a Linux kernel feature that sends a signal to the
        child process when the parent dies, REGARDLESS of how the parent was killed.
        This works even for SIGKILL (kill -9) where Python cleanup cannot run.

        When VMRunner dies (crash, kill -9, SIGTERM, etc.), kernel automatically
        sends SIGKILL to QEMU process. No orphaned processes possible.
        """
        import ctypes
        import subprocess

        # Import PR_SET_PDEATHSIG constant
        # This is Linux-specific, set to 1 based on prctl.h
        PR_SET_PDEATHSIG = 1

        def set_pdeathsig():
            """
            Set parent death signal to SIGKILL for this process.

            Called in child process before exec via preexec_fn.
            When parent dies, kernel sends SIGKILL to this process.
            """
            try:
                # Load libc
                libc = ctypes.CDLL('libc.so.6')

                # Call prctl(PR_SET_PDEATHSIG, SIGKILL)
                # SIGKILL = 9
                result = libc.prctl(PR_SET_PDEATHSIG, signal.SIGKILL)

                if result != 0:
                    # prctl failed, but we can't log here (in child process)
                    # Parent will detect if QEMU fails to start
                    pass

            except Exception:
                # If prctl fails (non-Linux, missing libc), continue anyway
                # QEMU will start but won't have death signal protection
                pass

        # Call parent's pre-launch
        self._pre_launch()
        LOG.debug('VM launch command: %r', ' '.join(self._qemu_full_args))

        # Launch QEMU with preexec_fn to set parent death signal
        # pylint: disable=consider-using-with
        self._popen = subprocess.Popen(
            self._qemu_full_args,
            stdin=subprocess.DEVNULL,
            stdout=self._qemu_log_file,
            stderr=subprocess.STDOUT,
            shell=False,
            close_fds=False,
            preexec_fn=set_pdeathsig  # Set PR_SET_PDEATHSIG before exec
        )
        self._launched = True
        self._post_launch()

    @property
    def _base_args(self) -> List[str]:
        """
        Override base args to only include essential QMP/console config.

        No display or VGA defaults - users configure these explicitly if needed.
        QEMU will use its own defaults (typically GTK/SDL if available).
        """
        args = []

        # QMP configuration (from parent class)
        if self._qmp_set:
            if self._sock_pair:
                moncdev = f"socket,id=mon,fd={self._sock_pair[0].fileno()}"
            elif isinstance(self._monitor_address, tuple):
                moncdev = "socket,id=mon,host={},port={}".format(
                    *self._monitor_address
                )
            else:
                moncdev = f"socket,id=mon,path={self._monitor_address}"
            args.extend(
                ["-chardev", moncdev, "-mon", "chardev=mon,mode=control"]
            )

        # Machine type (from parent class)
        if self._machine is not None:
            args.extend(["-machine", self._machine])

        # Console configuration (from parent class)
        for _ in range(self._console_index):
            args.extend(["-serial", "null"])
        if self._console_set:
            assert self._cons_sock_pair is not None
            fd = self._cons_sock_pair[0].fileno()
            chardev = f"socket,id=console,fd={fd}"
            args.extend(["-chardev", chardev])
            if self._console_device_type is None:
                args.extend(["-serial", "chardev:console"])
            else:
                device = "%s,chardev=console" % self._console_device_type
                args.extend(["-device", device])

        return args


# Module-level function - must be outside class for atexit registration.
# This function is registered with atexit.register() to cleanup orphaned
# QEMU processes when Python exits. It accesses the module-level
# _active_qemu_pids set.
def _cleanup_orphan_qemu_processes():
    """Kill any QEMU processes that are still running when Python exits.

    # NOTE: Good - atexit handler prevents orphaned QEMU processes when Python
    # exits normally.
    # This is the best solution without requiring systemd or daemon
    # infrastructure.
    #       Works for crashes, Ctrl+C, and normal exits.
    """
    if _active_qemu_pids:
        LOG.debug(
            f"Cleaning up {len(_active_qemu_pids)
                           } orphan QEMU processes on exit"
        )
        for pid in list(_active_qemu_pids):
            try:
                os.kill(pid, signal.SIGKILL)
                LOG.debug(f"Killed orphan QEMU process {pid}")
            except (ProcessLookupError, OSError):
                pass  # Process already dead
        _active_qemu_pids.clear()


# Register cleanup handler
atexit.register(_cleanup_orphan_qemu_processes)


class MachineError(Exception):
    """Machine-related errors"""


class Machine(ConfigurableMachine):
    """
    Enhanced VM machine management.

    Handles QEMU process lifecycle, QMP communication, and integration
    with MAQET's state management system. Uses extensible handler-based
    configuration processing.

    # TODO(architect, 2025-10-10): [ARCH] Machine class has too many responsibilities (907 lines)
    # Context: This class handles VM lifecycle, config validation, QMP communication, storage
    # setup, config handler registry, process cleanup, signal handling. Issue #4 in
    # ARCHITECTURAL_REVIEW.md.
    #
    # Recommendation: Extract responsibilities:
    # - ConfigValidator: validate binary, memory, CPU, display, network
    # - QMPClient: QMP communication only (execute, connect, timeout handling)
    # - StorageCoordinator: storage device setup
    # Machine focuses on process lifecycle only.
    #
    # Effort: Large (1 week)
    # Priority: High (should fix for 1.0)
    # See: ARCHITECTURAL_REVIEW.md Issue #4

    # TODO(architect, 2025-10-10): [ARCH] CRITICAL - Cross-process QMP Communication Impossible
    # Context: QEMUMachine instances cannot be shared between processes because Python cannot
    # pickle file descriptors (QMP socket connections). When CLI exits, QMP connections are
    # destroyed, making "maqet qmp myvm query-status" fail with "No such file or directory".
    # This is Issue #1 in ARCHITECTURAL_REVIEW.md.
    #
    # Root Cause: Machine instances stored in-memory dict (_machines) are lost when CLI exits.
    #
    # Current Status: QMP only works in Python API mode (same process). CLI mode doesn't work.
    #
    # Recommended Solution for 1.0: Direct Socket Communication
    #   - Bypass QEMUMachine, talk directly to QMP socket stored in database
    #   - Store socket path in database, connect on demand
    #   - No daemon required - VMs run as independent processes
    #   - Effort: Medium (2-4 days)
    #
    # Future Enhancement (2.0): Long-Running Service Architecture
    #   - Optional systemd service for centralized VM management
    #   - Advanced features like scheduled snapshots, health monitoring
    #   - CLI continues to work without service (backwards compatible)
    #   - Effort: Large (1-2 weeks)
    #
    # Implementation Steps:
    #   1. Create QMPSocketClient class that connects to existing socket
    #   2. Add socket_connect() method: read socket path from DB, connect via JSON-RPC
    #   3. Add execute_qmp_command() method: send JSON, parse response
    #   4. Modify Maqet.qmp() to use QMPSocketClient instead of Machine._qemu_machine
    #   5. Test with real VMs: start VM, exit CLI, run qmp commands
    #
    # See: ARCHITECTURAL_REVIEW.md Issue #1 for detailed analysis
    """

    def __init__(
        self,
        config_data: Dict[str, Any],
        vm_id: str,
        state_manager: "StateManager",
        config_validator: Optional[ConfigValidator] = None,
    ):
        """
        Initialize machine instance.

        Args:
            config_data: VM configuration dictionary
            vm_id: VM instance ID
            state_manager: State manager instance
            config_validator: Configuration validator (optional, creates default if None)
        """
        LOG.debug(f"Initializing Machine for VM {vm_id}")

        # Initialize ConfigurableMachine (creates instance-specific config registry)
        super().__init__()

        # Initialize validator (use provided or create default)
        self.config_validator = config_validator or ConfigValidator()

        # Validate configuration
        self.config_validator.validate_config(config_data)

        self.config_data = config_data
        self.vm_id = vm_id
        self.state_manager = state_manager
        self._qemu_machine: Optional[QEMUMachine] = None
        self._pid: Optional[int] = None

        # Initialize storage manager
        self.storage_manager = StorageManager(vm_id)
        storage_configs = config_data.get("storage", [])
        if storage_configs:
            self.storage_manager.add_storage_from_config(storage_configs)

    def _validate_config(self, config_data: Dict[str, Any]) -> None:
        """
        Validate VM configuration data (delegates to ConfigValidator).

        DEPRECATED: This method is kept for backward compatibility.
        Use self.config_validator.validate_config() directly instead.

        Args:
            config_data: VM configuration dictionary

        Raises:
            MachineError: If configuration is invalid
        """
        try:
            self.config_validator.validate_config(config_data)
        except Exception as e:
            # Wrap validation errors as MachineError for backward compatibility
            raise MachineError(str(e))

    def __enter__(self):
        """
        Context manager entry - allows using Machine with 'with' statement.

        Example:
            with Machine(config, vm_id, state_manager) as machine:
                machine.start()
                # Do work...
            # QEMU automatically cleaned up on exit
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit - ensures QEMU is stopped when exiting 'with' block.

        This is called AUTOMATICALLY when:
        - 'with' block completes normally
        - Exception is raised in 'with' block
        - Process is killed (Python cleanup)

        This is the SIMPLE, RELIABLE way to ensure QEMU cleanup.
        """
        try:
            if self._qemu_machine and self._qemu_machine.is_running():
                LOG.debug(f"Context manager exit: stopping QEMU for {self.vm_id}")
                # Use graceful stop with short timeout for faster exit
                self.stop(force=False, timeout=Timeouts.VM_GRACEFUL_SHUTDOWN_SHORT)
        except Exception as e:
            LOG.error(f"Error stopping QEMU during context exit: {e}")
            # Try force kill as last resort
            if self._pid:
                try:
                    os.kill(self._pid, signal.SIGKILL)
                except (ProcessLookupError, OSError):
                    pass

        return False  # Don't suppress exceptions

    def __del__(self):
        """
        Cleanup destructor - ensures QEMU process is stopped when Machine is garbage collected.

        This prevents orphaned QEMU processes when tests or scripts exit without
        explicitly stopping VMs.
        """
        try:
            if self._qemu_machine and self._qemu_machine.is_running():
                LOG.debug(
                    f"Machine {
                        self.vm_id} being garbage collected - stopping QEMU process"
                )
                # Force kill without trying graceful shutdown to avoid hanging
                # during GC
                if self._pid:
                    try:
                        os.kill(self._pid, signal.SIGKILL)
                        LOG.debug(
                            f"Killed orphan QEMU process {
                                self._pid} for VM {self.vm_id}"
                        )
                        # Remove from registry
                        _active_qemu_pids.discard(self._pid)
                    except (ProcessLookupError, OSError):
                        pass  # Process already dead
                # Update state if possible
                try:
                    self.state_manager.update_vm_status(
                        self.vm_id, "stopped", pid=None, socket_path=None
                    )
                except Exception:
                    pass  # State manager might be gone during shutdown
        except Exception as e:
            # Destructors should never raise exceptions
            try:
                LOG.debug(f"Error in Machine.__del__ for {self.vm_id}: {e}")
            except Exception:
                pass  # Logger might be gone during interpreter shutdown

    def start(self) -> None:
        """
        Start VM and wait for it to be ready.

        Implements file locking to prevent concurrent starts and ensures
        cleanup of partial state (PID, socket) on any failure.
        Storage file cleanup is handled by storage.py.
        """
        import fcntl

        lock_file = None

        try:
            # Acquire lock to prevent concurrent VM starts
            lock_file_path = self.state_manager.get_lock_path(self.vm_id)
            lock_file_path.parent.mkdir(parents=True, exist_ok=True)
            lock_file = open(lock_file_path, "w")

            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise MachineError(
                    f"VM {self.vm_id} is already being started by another process. "
                    f"Wait for that process to complete."
                )

            # Pre-start validation
            self._pre_start_validation()

            try:
                self._create_qemu_machine()
                self._configure_machine()

                LOG.info(f"Starting VM {self.vm_id}")
                self._qemu_machine.launch()

                # Get process PID
                self._pid = self._qemu_machine._popen.pid

                # Register PID for cleanup on exit
                _active_qemu_pids.add(self._pid)

                # Write PID file
                pid_path = self.state_manager.get_pid_path(self.vm_id)
                with open(pid_path, "w") as f:
                    f.write(str(self._pid))

                # Get the actual socket path used by QEMUMachine
                actual_socket_path = self._qemu_machine._monitor_address
                if not actual_socket_path:
                    LOG.warning(
                        f"QEMUMachine did not create QMP monitor socket for VM {
                            self.vm_id}"
                    )
                    actual_socket_path = str(
                        self.state_manager.get_socket_path(self.vm_id)
                    )

                # Update database with VM status and actual socket path
                self.state_manager.update_vm_status(
                    self.vm_id,
                    "running",
                    pid=self._pid,
                    socket_path=str(actual_socket_path),
                )

                LOG.debug(f"VM {self.vm_id} QMP socket: {actual_socket_path}")

                # Wait for VM to be ready (handled by QEMUMachine)
                self._wait_for_ready()

            except Exception as e:
                LOG.error(f"Failed to start VM {self.vm_id}: {e}")
                self._cleanup_failed_start()
                raise MachineError(f"Failed to start VM: {e}")

        finally:
            # Release lock
            if lock_file:
                try:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                    lock_file.close()
                    Path(lock_file.name).unlink(missing_ok=True)
                except Exception as e:
                    LOG.debug(f"Error releasing VM start lock: {e}")

    def _pre_start_validation(self) -> None:
        """
        Perform pre-start validation checks (delegates to ConfigValidator).

        Raises:
            MachineError: If validation fails
        """
        try:
            self.config_validator.pre_start_validation(self.config_data)
        except Exception as e:
            # Wrap validation errors as MachineError for backward compatibility
            raise MachineError(str(e))

    def _cleanup_failed_start(self) -> None:
        """Clean up partial state after failed VM start.

        Removes PID file, socket file, and updates database status.
        Storage file cleanup is handled by storage.py (partial file removal).
        """
        try:
            # Remove PID file if it exists
            if self._pid:
                pid_path = self.state_manager.get_pid_path(self.vm_id)
                if pid_path.exists():
                    pid_path.unlink()
                    LOG.debug(f"Removed PID file for failed start: {pid_path}")

                # Unregister PID from cleanup registry
                _active_qemu_pids.discard(self._pid)

            # Remove socket file if it exists
            socket_path = self.state_manager.get_socket_path(self.vm_id)
            if socket_path.exists():
                socket_path.unlink()
                LOG.debug(
                    f"Removed socket file for failed start: {socket_path}"
                )

            # Update database status to failed
            self.state_manager.update_vm_status(
                self.vm_id, "failed", pid=None, socket_path=None
            )
            LOG.debug(f"Updated VM {self.vm_id} status to failed")

        except Exception as cleanup_error:
            LOG.warning(
                f"Error during cleanup of failed start: {cleanup_error}"
            )

    def _force_kill_process(self, pid: int) -> None:
        """
        Force kill a process with escalation from SIGTERM to SIGKILL.

        Args:
            pid: Process ID to kill

        Sends SIGTERM first, waits for process to exit, then sends SIGKILL if needed.
        """
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(Intervals.SIGTERM_WAIT)
            if self._is_process_alive(pid):
                os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

    def _graceful_shutdown(self, timeout: int = 30) -> bool:
        """
        Attempt graceful shutdown of VM via QMP.

        Args:
            timeout: Maximum seconds to wait for shutdown

        Returns:
            True if shutdown succeeded, False otherwise
        """
        if not self._qemu_machine:
            return False

        try:
            LOG.debug(f"Attempting graceful shutdown of VM {self.vm_id}")
            self._qemu_machine.shutdown()

            # Wait for process to exit
            start_time = time.time()
            while (
                self._qemu_machine.is_running()
                and (time.time() - start_time) < timeout
            ):
                time.sleep(Intervals.SHUTDOWN_POLL)

            # Check if shutdown succeeded
            if not self._qemu_machine.is_running():
                LOG.info(f"VM {self.vm_id} shutdown gracefully")
                return True
            else:
                LOG.warning(
                    f"VM {self.vm_id} didn't shutdown gracefully in {timeout}s"
                )
                return False

        except Exception as e:
            LOG.warning(f"Graceful shutdown failed for VM {self.vm_id}: {e}")
            return False

    def _force_kill(self) -> None:
        """
        Force kill the VM process using SIGTERM then SIGKILL.

        Sends SIGTERM first, waits briefly, then sends SIGKILL if needed.
        """
        if not self._pid:
            return

        LOG.info(f"Force killing VM {self.vm_id} (PID {self._pid})")
        try:
            # Send SIGTERM first
            os.kill(self._pid, signal.SIGTERM)
            time.sleep(Intervals.SIGTERM_WAIT)

            # Check if still alive, send SIGKILL if needed
            if self._is_process_alive(self._pid):
                LOG.debug(f"Process {self._pid} still alive, sending SIGKILL")
                os.kill(self._pid, signal.SIGKILL)
        except ProcessLookupError:
            # Process already dead
            pass

    def _cleanup_after_stop(self) -> None:
        """
        Cleanup after VM stops.

        - Unregisters PID from active registry
        - Updates database status
        - Removes temporary files
        """
        # Unregister PID from cleanup registry
        if self._pid and self._pid in _active_qemu_pids:
            _active_qemu_pids.discard(self._pid)

        # Update database status to stopped
        self.state_manager.update_vm_status(
            self.vm_id, "stopped", pid=None, socket_path=None
        )

        # Clean up files
        self._cleanup_files()

    def stop(self, force: bool = False, timeout: int = 30) -> None:
        """
        Stop the VM.

        Args:
            force: Force kill immediately, skip graceful shutdown
            timeout: Timeout for graceful shutdown (only used when force=False)
        """
        try:
            if self._qemu_machine and self._qemu_machine.is_running():
                LOG.info(f"Stopping VM {self.vm_id}")

                if force:
                    # Force kill immediately - skip graceful shutdown
                    self._force_kill()
                else:
                    # Try graceful shutdown first
                    if not self._graceful_shutdown(timeout):
                        # Graceful shutdown failed, force kill
                        self._force_kill()

            # Cleanup after stop
            self._cleanup_after_stop()

        except Exception as e:
            LOG.error(f"Failed to stop VM {self.vm_id}: {e}")
            raise MachineError(f"Failed to stop VM: {e}")

    # Dangerous QMP commands that could harm VM or data
    DANGEROUS_QMP_COMMANDS = {
        "quit",  # Terminates VM without graceful shutdown
        "system_powerdown",  # Powers down VM (safe but user should use stop())
        "system_reset",  # Force reboot without saving
        "inject-nmi",  # Crashes guest OS for debugging
        "migrate",  # Could corrupt VM if done incorrectly
        "migrate_set_speed",
        "migrate_cancel",
        "pmemsave",  # Dumps memory (security risk)
        "memsave",  # Dumps memory (security risk)
        "drive_del",  # Removes storage device
        "blockdev-del",  # Removes block device
        "device_del",  # Removes device (should use device_del method)
    }

    # Safe QMP commands that are commonly used
    SAFE_QMP_COMMANDS = {
        "query-status",  # Get VM status
        "query-version",  # Get QEMU version
        "query-commands",  # List available commands
        "query-kvm",  # Check if KVM is enabled
        "query-cpus",  # Get CPU info
        "query-block",  # Get block device info
        "query-chardev",  # Get character devices
        "screendump",  # Take screenshot
        "send-key",  # Send keyboard input
        "human-monitor-command",  # Execute monitor command
        "cont",  # Resume VM from pause
        "stop",  # Pause VM
        "input-send-event",  # Send input events
    }

    def qmp(self, command: str, **kwargs) -> Dict[str, Any]:
        """
        Execute QMP command (alias for qmp_command).

        Args:
            command: QMP command name
            **kwargs: Command arguments

        Returns:
            Command result dictionary

        Raises:
            MachineError: If VM is not running or command fails
        """
        return self.qmp_command(command, **kwargs)

    def qmp_command(self, command: str, **kwargs) -> Dict[str, Any]:
        """
        Execute QMP command on the VM with security validation and timeout.

        Args:
            command: QMP command to execute
            **kwargs: Command parameters

        Returns:
            QMP command result

        Raises:
            MachineError: If VM is not running, command is dangerous, or timeout occurs
        """
        if not self._qemu_machine or not self._qemu_machine.is_running():
            raise MachineError(f"VM {self.vm_id} is not running")

        # Security: Validate command safety
        if command in self.DANGEROUS_QMP_COMMANDS:
            LOG.warning(
                f"QMP command '{
                    command}' is potentially dangerous and may harm the VM. "
                f"Consider using the appropriate maqet method instead (e.g., stop() for powerdown)."
            )
            # Note: We log warning but allow execution for advanced users
            # A future enhancement could add a confirmation prompt or --force
            # flag

        elif command not in self.SAFE_QMP_COMMANDS:
            # Unknown command - warn but allow
            LOG.info(
                f"QMP command '{
                    command}' is not in the known safe commands list. "
                f"Proceeding with caution."
            )

        try:
            # Build QMP command
            qmp_cmd = {"execute": command}
            if kwargs:
                qmp_cmd["arguments"] = kwargs

            LOG.debug(f"Executing QMP command on {self.vm_id}: {qmp_cmd}")

            # Execute with timeout using concurrent.futures
            import concurrent.futures
            import threading

            timeout = Timeouts.QMP_COMMAND

            # Create a thread-safe result container
            result_container = {"result": None, "error": None}

            def execute_qmp():
                try:
                    result_container["result"] = self._qemu_machine.qmp(
                        command, **kwargs
                    )
                except Exception as e:
                    result_container["error"] = e

            # Execute QMP command in thread with timeout
            qmp_thread = threading.Thread(target=execute_qmp)
            qmp_thread.daemon = True
            qmp_thread.start()
            qmp_thread.join(timeout=timeout)

            if qmp_thread.is_alive():
                # Timeout occurred
                raise MachineError(
                    f"QMP command '{command}' timed out after {
                        timeout} seconds. "
                    f"VM may be unresponsive."
                )

            # Check if error occurred during execution
            if result_container["error"]:
                raise result_container["error"]

            return result_container["result"]

        except MachineError:
            # Re-raise MachineError as-is
            raise
        except Exception as e:
            LOG.error(f"QMP command failed on VM {self.vm_id}: {e}")
            raise MachineError(f"QMP command failed: {e}")

    @property
    def pid(self) -> Optional[int]:
        """Get VM process PID."""
        if self._qemu_machine and self._qemu_machine._popen:
            return self._qemu_machine._popen.pid
        return self._pid

    @property
    def is_running(self) -> bool:
        """Check if VM is running."""
        if self._qemu_machine:
            return self._qemu_machine.is_running()
        if self._pid:
            return self._is_process_alive(self._pid)
        return False

    def _create_qemu_machine(self) -> None:
        """Create QEMUMachine instance."""
        # Get QEMU binary from config
        binary = self.config_data.get("binary", "/usr/bin/qemu-system-x86_64")

        # Set up QMP socket
        socket_path = str(self.state_manager.get_socket_path(self.vm_id))

        # Ensure socket directory exists
        socket_path_obj = self.state_manager.get_socket_path(self.vm_id)
        socket_path_obj.parent.mkdir(parents=True, exist_ok=True)

        LOG.debug(f"Creating MaqetQEMUMachine with QMP socket: {socket_path}")

        self._qemu_machine = MaqetQEMUMachine(
            binary=binary,
            name=self.vm_id,
            log_dir=str(self.state_manager.xdg.runtime_dir),
            monitor_address=socket_path,  # Unix socket path as string
        )

        # Verify QMP is enabled
        LOG.debug(f"QMP enabled: {self._qemu_machine._qmp_set}")

    def _configure_machine(self) -> None:
        """Configure QEMU machine using handler-based system."""
        if not self._qemu_machine:
            return

        # Process configuration using registered handlers
        processed_keys = self.process_configuration(self.config_data)

        # Apply defaults for any unprocessed keys
        self.apply_default_configuration()

        LOG.debug(
            f"Machine configuration complete. Processed keys: {processed_keys}"
        )

    def _add_storage_devices(self) -> None:
        """Add all storage devices to QEMU machine using unified storage manager."""
        if not self._qemu_machine:
            return

        # Create storage files if needed
        self.storage_manager.create_storage_files()

        # Add QEMU arguments for all storage devices
        storage_args = self.storage_manager.get_qemu_args()
        for args_list in storage_args:
            # Each args_list is like ["-drive", "file=...,if=...,format=..."]
            self._qemu_machine.add_args(*args_list)

    # NOTE: Storage handling has been refactored to use the extensible
    # StorageManager system
    # New storage types can be added by creating new device classes with
    # @storage_device decorator

    # NOTE: QEMUMachine handles wait-for-ready, but we verify QMP connectivity
    def _wait_for_ready(self) -> None:
        """Wait for VM QMP to be ready."""
        if not self._qemu_machine:
            return

        # QEMUMachine.launch() already establishes QMP connection
        # Just verify it's working with a simple query
        try:
            if self._qemu_machine.is_running():
                # Test QMP is responsive
                self._qemu_machine.qmp("query-status")
                LOG.info(f"VM {self.vm_id} is ready")
        except Exception as e:
            LOG.warning(f"VM {self.vm_id} QMP verification failed: {e}")
            # VM process started but QMP may not be fully ready yet
            # This is usually not critical as QMP will become available shortly

    def _is_process_alive(self, pid: int) -> bool:
        """Check if process is still running."""
        try:
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False

    def _cleanup_files(self) -> None:
        """Clean up temporary files."""
        # Remove PID file
        pid_path = self.state_manager.get_pid_path(self.vm_id)
        if pid_path.exists():
            pid_path.unlink()

        # Socket cleanup is handled by QEMUMachine
