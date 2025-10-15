"""
VM Manager

Manages VM lifecycle operations: add, start, stop, remove, list.
Extracted from Maqet class to follow Single Responsibility Principle.
"""

import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..config import ConfigMerger
from ..constants import Intervals, Timeouts
from ..exceptions import (
    ConfigurationError,
    RunnerSpawnError,
    StateError,
    VMAlreadyExistsError,
    VMLifecycleError,
    VMNotFoundError,
    VMNotRunningError,
    VMStartError,
    VMStopError,
)
from ..logger import LOG
from ..state import StateManager, VMInstance

# Legacy exception alias (backward compatibility)
VMManagerError = VMLifecycleError
ConfigError = ConfigurationError
StateManagerError = StateError


class VMManager:
    """
    Manages VM lifecycle operations.

    Responsibilities:
    - Create VMs (add)
    - Start VMs (spawn runner processes)
    - Stop VMs (via IPC or process kill)
    - Remove VMs (from database)
    - List VMs
    - Clean up dead processes
    """

    def __init__(self, state_manager: StateManager, config_parser):
        """
        Initialize VM manager.

        Args:
            state_manager: State management instance
            config_parser: Configuration parser instance
        """
        self.state_manager = state_manager
        self.config_parser = config_parser
        LOG.debug("VMManager initialized")

    def add(
        self,
        config: Optional[Union[str, List[str]]] = None,
        name: Optional[str] = None,
        empty: bool = False,
        **kwargs,
    ) -> str:
        """
        Create a new VM from configuration file(s) or parameters.

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
            VMManagerError: If VM creation fails

        Examples:
            Single config: add(config="vm.yaml", name="myvm")
            Multiple configs: add(
                config=["base.yaml", "custom.yaml"], name="myvm"
            )
            Config + params: add(config="base.yaml", memory="8G", cpu=4)
            Empty VM: add(name="placeholder-vm", empty=True)
        """
        try:
            # Layer 2: Extract client working directory for path resolution
            client_cwd = kwargs.pop("_client_cwd", None)

            # Handle empty VM creation
            if empty:
                # Validate that no config or kwargs are provided with --empty
                if config:
                    raise VMManagerError(
                        "Cannot specify config files with --empty flag"
                    )
                if kwargs:
                    raise VMManagerError(
                        "Cannot specify configuration parameters "
                        "with --empty flag"
                    )

                # Create completely empty config
                config_data = {}
                config_file = None

                # Generate name if not provided
                if not name:
                    # Generate unique name using UUID without creating temp VM
                    import uuid
                    unique_suffix = str(uuid.uuid4()).split('-')[-1][:8]
                    name = f"empty-vm-{unique_suffix}"

                # Skip validation for empty VMs
                # Create VM in database with empty config
                vm_id = self.state_manager.create_vm(
                    name, config_data, config_file
                )

                return vm_id

            # Normal VM creation path
            # Load and deep-merge configuration files
            if config:
                config_data = ConfigMerger.load_and_merge_files(config)
                if isinstance(config, str):
                    config_file = config
                elif config:
                    config_file = config[0]
                else:
                    config_file = None
            else:
                config_data = {}
                config_file = None

            # Merge kwargs with config data (kwargs take precedence)
            if kwargs:
                config_data = ConfigMerger.deep_merge(config_data, kwargs)

            # Handle name priority: CLI --name > config name > auto-generated
            if not name:
                # Check if name is present in merged config
                name = config_data.get("name")

            # Always remove name from config_data as it's VM metadata, not QEMU
            # config
            if "name" in config_data:
                config_data = {
                    k: v for k, v in config_data.items() if k != "name"
                }

            # Generate name if still not provided
            if not name:
                # Generate unique name using UUID without creating temp VM
                import uuid
                unique_suffix = str(uuid.uuid4()).split('-')[-1][:8]
                name = f"vm-{unique_suffix}"

            # Validate the final merged configuration
            config_data = self.config_parser.validate_config(config_data)

            # Create VM in database
            vm_id = self.state_manager.create_vm(
                name, config_data, config_file
            )

            return vm_id

        # Specific exception handlers for better error messages
        except FileNotFoundError as e:
            raise VMManagerError(
                f"Configuration file not found: {e.filename}. "
                f"Check that the file path is correct."
            )
        except PermissionError as e:
            raise VMManagerError(
                f"Permission denied accessing configuration file: {
                    e.filename}. "
                f"Check file permissions and ownership."
            )
        except ConfigError as e:
            raise VMManagerError(f"Configuration error: {e}")
        except StateManagerError as e:
            raise VMManagerError(f"Database error: {e}")
        except Exception as e:
            # Last resort - log unexpected errors with context
            LOG.error(
                f"Unexpected error creating VM: {type(e).__name__}: {e}",
                exc_info=True,
            )
            raise VMManagerError(f"Failed to create VM: {e}")

    def start(self, vm_id: str) -> VMInstance:
        """
        Start a virtual machine by spawning a detached VM runner process.

        Changes from previous implementation:
        - No longer manages Machine directly
        - Spawns VM runner process that manages QEMU lifecycle
        - VM runner survives CLI exit
        - Returns immediately after runner is ready

        Args:
            vm_id: VM identifier (name or ID)

        Returns:
            VM instance information

        Raises:
            VMManagerError: If VM start fails
        """
        try:
            # Get VM from database
            vm = self.state_manager.get_vm(vm_id)
            if not vm:
                raise VMManagerError(f"VM '{vm_id}' not found")

            # Check if VM is already running
            if vm.status == "running":
                # Check if runner process is actually alive
                from ..process_spawner import is_runner_alive

                if vm.runner_pid and is_runner_alive(vm.runner_pid):
                    raise VMManagerError(
                        f"VM '{vm_id}' is already running "
                        f"(runner PID: {vm.runner_pid})"
                    )
                else:
                    # Stale state - clean up and continue
                    LOG.warning(
                        f"VM '{vm_id}' has stale 'running' status, cleaning up"
                    )
                    self.state_manager.update_vm_status(
                        vm_id, "stopped", runner_pid=None, socket_path=None
                    )

            # Check if VM has required configuration
            if not vm.config_data or not vm.config_data.get("binary"):
                raise VMManagerError(
                    f"VM '{vm_id}' cannot be started: missing required "
                    f"configuration. Use 'maqet apply {vm_id} "
                    f"--config <config.yaml>' to add configuration."
                )

            # Spawn VM runner process
            from ..process_spawner import (
                spawn_vm_runner,
                wait_for_vm_ready,
                get_socket_path,
            )

            try:
                # Get database path for runner
                db_path = self.state_manager.xdg.database_path

                runner_pid = spawn_vm_runner(vm.id, db_path, timeout=Timeouts.PROCESS_SPAWN)
                LOG.info(f"Spawned VM runner process for '{vm_id}' (PID: {runner_pid})")
            except Exception as e:
                raise VMManagerError(f"Failed to spawn VM runner: {e}")

            # Wait for VM runner to be ready (socket available)
            socket_path = get_socket_path(vm.id)
            ready = wait_for_vm_ready(vm.id, socket_path, timeout=Timeouts.VM_START)

            if not ready:
                # Runner process started but socket not available - cleanup
                from ..process_spawner import kill_runner

                kill_runner(runner_pid, force=True)
                raise VMManagerError("VM runner did not become ready within timeout")

            # Verify VM is actually running (runner updated DB)
            vm_updated = self.state_manager.get_vm(vm_id)
            if vm_updated.status != "running":
                raise VMManagerError(
                    f"VM runner started but VM status is '{vm_updated.status}'"
                )

            return vm_updated

        except Exception as e:
            raise VMManagerError(f"Failed to start VM '{vm_id}': {e}")

    def stop(
        self, vm_id: str, force: bool = False, timeout: int = 30
    ) -> VMInstance:
        """
        Stop a VM by sending stop command to VM runner or killing runner process.

        Changes from previous implementation:
        - No longer uses Machine.stop() directly
        - Sends stop command via IPC (graceful)
        - Falls back to killing runner process if IPC fails

        Args:
            vm_id: VM identifier (name or ID)
            force: If True, kill runner immediately (SIGKILL).
                   If False, graceful shutdown (SIGTERM)
            timeout: Timeout for graceful shutdown (ignored for now)

        Returns:
            VM instance information

        Raises:
            VMManagerError: If VM stop fails
        """
        try:
            # Get VM from database
            vm = self.state_manager.get_vm(vm_id)
            if not vm:
                raise VMManagerError(f"VM '{vm_id}' not found")

            # Check if VM is running
            if vm.status != "running":
                LOG.info(f"VM '{vm_id}' is not running (status: {vm.status})")
                # Ensure status is "stopped" (not "created", etc.)
                if vm.status != "stopped":
                    self.state_manager.update_vm_status(
                        vm_id, "stopped", pid=None, runner_pid=None, socket_path=None
                    )
                    vm = self.state_manager.get_vm(vm_id)
                return vm

            from ..process_spawner import is_runner_alive, kill_runner
            from ..ipc.runner_client import RunnerClient, RunnerClientError

            # Verify runner process exists
            if not vm.runner_pid or not is_runner_alive(vm.runner_pid):
                # Runner missing/dead - check for orphaned QEMU process
                LOG.warning(
                    f"VM '{vm_id}' runner process not found, checking for orphaned QEMU"
                )

                # Fallback: Kill orphaned QEMU process if it exists
                if vm.pid:
                    try:
                        # Check if QEMU process is alive
                        os.kill(vm.pid, 0)  # Signal 0 checks existence

                        # QEMU is alive - kill it
                        LOG.warning(
                            f"Found orphaned QEMU process (PID {vm.pid}), "
                            f"terminating it"
                        )
                        if force:
                            os.kill(vm.pid, 9)  # SIGKILL
                        else:
                            os.kill(vm.pid, 15)  # SIGTERM

                        # Wait briefly for process to die
                        time.sleep(0.5)

                    except ProcessLookupError:
                        # QEMU process already dead, no action needed
                        LOG.debug(f"QEMU process {vm.pid} already dead")
                    except PermissionError:
                        LOG.error(
                            f"Permission denied when killing QEMU process {vm.pid}"
                        )
                    except Exception as e:
                        LOG.error(f"Failed to kill QEMU process {vm.pid}: {e}")

                # Clean up DB
                self.state_manager.update_vm_status(
                    vm_id, "stopped", pid=None, runner_pid=None, socket_path=None
                )
                return self.state_manager.get_vm(vm_id)

            # Try graceful stop via IPC (if not force)
            if not force:
                client = RunnerClient(vm.id, self.state_manager)

                try:
                    result = client.send_command("stop", timeout=timeout)
                    LOG.info(f"VM '{vm_id}' stopped gracefully via IPC")

                    # Wait briefly for runner to exit and update DB
                    time.sleep(Intervals.CLEANUP_WAIT)

                    # Verify status updated
                    vm_updated = self.state_manager.get_vm(vm_id)
                    return vm_updated

                except RunnerClientError as e:
                    LOG.warning(
                        f"IPC stop failed for '{vm_id}': {e}, "
                        f"falling back to SIGTERM"
                    )

            # Fallback: Kill runner process directly
            LOG.info(
                f"Killing VM runner process for '{vm_id}' "
                f"(PID: {vm.runner_pid}, force={force})"
            )
            killed = kill_runner(vm.runner_pid, force=force)

            if killed:
                # Wait briefly for cleanup
                time.sleep(Intervals.CLEANUP_WAIT)

                # Verify DB updated (runner should clean up on exit)
                vm_updated = self.state_manager.get_vm(vm_id)
                if vm_updated.status == "running":
                    # Runner didn't clean up - do it manually
                    self.state_manager.update_vm_status(
                        vm_id, "stopped", runner_pid=None, socket_path=None
                    )
                    vm_updated = self.state_manager.get_vm(vm_id)

                return vm_updated
            else:
                raise VMManagerError(f"Failed to kill runner process {vm.runner_pid}")

        except Exception as e:
            raise VMManagerError(f"Failed to stop VM '{vm_id}': {e}")

    def remove(
        self,
        vm_id: Optional[str] = None,
        force: bool = False,
        all: bool = False,
        clean_storage: bool = False,
    ) -> bool:
        """
        Remove a virtual machine completely.

        Args:
            vm_id: VM identifier (name or ID)
            force: Force removal even if VM is running
            all: Remove all virtual machines
            clean_storage: Also delete associated storage files

        Returns:
            True if removed successfully

        Raises:
            VMManagerError: If VM removal fails
        """
        try:
            # Validate arguments
            if all and vm_id:
                raise VMManagerError("Cannot specify both vm_id and --all flag")
            if not all and not vm_id:
                raise VMManagerError("Must specify either vm_id or --all flag")

            # Handle bulk removal
            if all:
                return self._remove_all_vms(force, clean_storage)

            # Handle single VM removal
            return self._remove_single_vm(vm_id, force, clean_storage)

        except Exception as e:
            raise VMManagerError(f"Failed to remove VM(s): {e}")

    def _remove_single_vm(
        self, vm_id: str, force: bool, clean_storage: bool = False
    ) -> bool:
        """Remove a single VM."""
        # Get VM from database
        vm = self.state_manager.get_vm(vm_id)
        if not vm:
            raise VMManagerError(f"VM '{vm_id}' not found")

        # Stop VM if running
        if vm.status == "running":
            if not force:
                raise VMManagerError(
                    f"VM '{vm_id}' is running. Use --force to remove "
                    f"running VMs"
                )
            self.stop(vm_id, force=True)

        # Clean up storage files if requested
        if clean_storage:
            storage_configs = vm.config_data.get("storage", [])
            for storage in storage_configs:
                if "file" in storage:
                    storage_path = Path(storage["file"])
                    if storage_path.exists():
                        try:
                            LOG.info(f"Removing storage file: {storage_path}")
                            storage_path.unlink()
                        except OSError as e:
                            LOG.warning(
                                f"Failed to remove storage file {
                                    storage_path}: {e}"
                            )

        # Remove from database
        removed = self.state_manager.remove_vm(vm_id)
        if not removed:
            raise VMManagerError(f"Failed to remove VM '{vm_id}' from database")

        return True

    def _remove_all_vms(
        self, force: bool, clean_storage: bool = False
    ) -> bool:
        """Remove all VMs with confirmation."""
        # Get all VMs
        all_vms = self.state_manager.list_vms()

        if not all_vms:
            print("No virtual machines found.")
            return True

        # Display VMs that will be removed
        print(f"Found {len(all_vms)} virtual machine(s) to remove:")
        print()

        # Create table header
        header = f"{'NAME':<20} {'STATUS':<10} {'PID':<8}"
        separator = "-" * 40
        print(header)
        print(separator)

        running_count = 0
        for vm in all_vms:
            pid_str = str(vm.pid) if vm.pid else "-"
            print(f"{vm.name:<20} {vm.status:<10} {pid_str:<8}")
            if vm.status == "running":
                running_count += 1

        print()

        # Show warning for running VMs
        if running_count > 0 and not force:
            print(
                f"WARNING: {running_count} VM(s) are currently running "
                f"and will be forcefully stopped."
            )
            print("Use --force to skip this warning in the future.")
            print()

        # Confirmation prompt
        try:
            response = (
                input(
                    f"Are you sure you want to remove ALL {len(all_vms)} "
                    f"virtual machines? [y/N]: "
                )
                .strip()
                .lower()
            )
        except (EOFError, KeyboardInterrupt):
            print("\nOperation cancelled.")
            return False

        if response not in ["y", "yes"]:
            print("Operation cancelled.")
            return False

        # Remove all VMs
        removed_count = 0
        failed_count = 0

        print()
        print("Removing virtual machines...")

        for vm in all_vms:
            try:
                # Stop VM if running
                if vm.status == "running":
                    try:
                        self.stop(vm.id, force=True)
                        print(f"  Stopped VM: {vm.name}")
                    except Exception as e:
                        print(f"  Warning: Failed to stop VM '{vm.name}': {e}")

                # Remove from database
                removed = self.state_manager.remove_vm(vm.id)
                if removed:
                    print(f"  Removed VM: {vm.name}")
                    removed_count += 1
                else:
                    print(f"  Failed to remove VM: {vm.name}")
                    failed_count += 1

            except Exception as e:
                print(f"  Error removing VM '{vm.name}': {e}")
                failed_count += 1

        print()
        print(
            f"Removal complete: {removed_count} removed, "
            f"{failed_count} failed"
        )

        if failed_count > 0:
            raise VMManagerError(f"Failed to remove {failed_count} VM(s)")

        return True

    def list_vms(self, status: Optional[str] = None) -> List[VMInstance]:
        """
        List virtual machines.

        Args:
            status: Filter by status ('running', 'stopped', 'created',
                'failed')

        Returns:
            List of VM instances
        """
        vms = self.state_manager.list_vms(status_filter=status)

        # Check process status and update if needed
        for vm in vms:
            if vm.status == "running" and vm.pid:
                if not self.state_manager._is_process_alive(vm.pid):
                    # Process doesn't exist, update status
                    self.state_manager.update_vm_status(
                        vm.id, "stopped", pid=None
                    )
                    vm.status = "stopped"
                    vm.pid = None

        return vms

    def cleanup_dead_processes(self) -> List[str]:
        """
        Check for VMs with running status but dead runner processes.
        Update DB to reflect reality.

        This runs on VMManager initialization to clean up stale state from
        crashed runners or improperly terminated VMs.

        Returns:
            List of VM IDs that were cleaned up
        """
        from ..process_spawner import is_runner_alive

        cleaned = []

        # Get all VMs marked as running
        all_vms = self.state_manager.list_vms()
        running_vms = [vm for vm in all_vms if vm.status == "running"]

        for vm in running_vms:
            if not vm.runner_pid or not is_runner_alive(vm.runner_pid):
                LOG.warning(
                    f"VM '{vm.name}' marked as running but runner process "
                    f"(PID: {vm.runner_pid}) is dead"
                )

                # Check for orphaned QEMU process
                if vm.pid:
                    try:
                        # Check if QEMU is alive
                        os.kill(vm.pid, 0)

                        # QEMU is alive - kill it
                        LOG.warning(
                            f"Found orphaned QEMU process (PID {vm.pid}) for VM "
                            f"'{vm.name}', terminating it"
                        )
                        os.kill(vm.pid, 9)  # SIGKILL
                        time.sleep(0.5)

                    except ProcessLookupError:
                        # QEMU already dead
                        LOG.debug(f"QEMU process {vm.pid} already dead")
                    except PermissionError:
                        LOG.error(
                            f"Permission denied when killing QEMU process {vm.pid}"
                        )
                    except Exception as e:
                        LOG.error(f"Failed to kill QEMU process {vm.pid}: {e}")

                # Update DB
                self.state_manager.update_vm_status(
                    vm.name, "stopped", pid=None, runner_pid=None, socket_path=None
                )
                cleaned.append(vm.id)

        return cleaned
