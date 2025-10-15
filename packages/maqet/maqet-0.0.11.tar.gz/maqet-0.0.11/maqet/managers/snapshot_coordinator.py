"""
Snapshot Coordinator

Coordinates snapshot operations across VM storage devices.
This manager handles snapshot lifecycle: create, load, list, and delete operations.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..constants import Defaults
from ..exceptions import (
    SnapshotCreationError,
    SnapshotDeleteError,
    SnapshotError,
    SnapshotLoadError,
    SnapshotNotFoundError,
    StorageDeviceNotFoundError,
    VMNotFoundError,
)
from ..logger import LOG
from ..snapshot import SnapshotManager
from ..state import StateManager, VMInstance
from ..storage import StorageManager

# Legacy exception alias (backward compatibility)
SnapshotCoordinatorError = SnapshotError


class SnapshotCoordinator:
    """
    Coordinates snapshot operations across VM storage devices.

    Responsibilities:
    - Create snapshots on QCOW2 storage devices
    - Restore/load snapshots
    - List available snapshots for VM drives
    - Route snapshot commands to appropriate operations
    - Integrate with storage management system

    This coordinator acts as a facade between the Maqet API and the
    underlying SnapshotManager implementation. It handles VM lookup,
    storage configuration, and error translation.
    """

    def __init__(self, state_manager: StateManager):
        """
        Initialize snapshot coordinator.

        Args:
            state_manager: State management instance for VM lookups
        """
        self.state_manager = state_manager
        LOG.debug("SnapshotCoordinator initialized")

    def snapshot(
        self,
        vm_id: str,
        action: str,
        drive: str,
        name: Optional[str] = None,
        overwrite: bool = False,
    ) -> Union[Dict[str, Any], List[str]]:
        """
        Main snapshot command router.

        Routes snapshot operations to appropriate handler based on action.
        This is the primary entry point for all snapshot operations.

        Args:
            vm_id: VM identifier (name or ID)
            action: Snapshot action ('create', 'load', 'list')
            drive: Storage drive name
            name: Snapshot name (required for create/load)
            overwrite: Overwrite existing snapshot (create only)

        Returns:
            Operation result dictionary or list of snapshots

        Raises:
            SnapshotCoordinatorError: If VM not found or operation fails
        """
        try:
            vm = self.state_manager.get_vm(vm_id)
            if not vm:
                raise SnapshotCoordinatorError(f"VM '{vm_id}' not found")

            # Create snapshot manager for this VM
            storage_manager = StorageManager(vm_id)
            storage_configs = vm.config_data.get("storage", [])
            if storage_configs:
                storage_manager.add_storage_from_config(storage_configs)
            snapshot_mgr = SnapshotManager(vm_id, storage_manager)

            # Route to appropriate action
            if action == "create":
                if not name:
                    raise SnapshotCoordinatorError(
                        "Snapshot name required for create action"
                    )
                return snapshot_mgr.create(drive, name, overwrite=overwrite)

            elif action == "load":
                if not name:
                    raise SnapshotCoordinatorError(
                        "Snapshot name required for load action"
                    )
                return snapshot_mgr.load(drive, name)

            elif action == "list":
                return snapshot_mgr.list(drive)

            else:
                raise SnapshotCoordinatorError(
                    f"Invalid action '{action}'. "
                    f"Available actions: create, load, list"
                )

        except SnapshotError as e:
            raise SnapshotCoordinatorError(f"Snapshot operation failed: {e}")
        except Exception as e:
            raise SnapshotCoordinatorError(
                f"Failed to manage snapshots for VM '{vm_id}': {e}"
            )

    def create(
        self, vm_id: str, drive: str, name: str, overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        Create snapshot on storage device.

        Args:
            vm_id: VM identifier (name or ID)
            drive: Storage drive name
            name: Snapshot name
            overwrite: Overwrite existing snapshot

        Returns:
            Operation result dictionary

        Raises:
            SnapshotCoordinatorError: If VM not found or operation fails
        """
        try:
            vm = self.state_manager.get_vm(vm_id)
            if not vm:
                raise SnapshotCoordinatorError(f"VM '{vm_id}' not found")

            # Create snapshot manager
            storage_manager = StorageManager(vm_id)
            storage_configs = vm.config_data.get("storage", [])
            if storage_configs:
                storage_manager.add_storage_from_config(storage_configs)
            snapshot_mgr = SnapshotManager(vm_id, storage_manager)

            # Create snapshot
            result = snapshot_mgr.create(drive, name, overwrite=overwrite)
            LOG.info(
                f"Created snapshot '{name}' on drive '{drive}' for VM '{vm_id}'"
            )
            return result

        except SnapshotError as e:
            raise SnapshotCoordinatorError(str(e))
        except Exception as e:
            raise SnapshotCoordinatorError(
                f"Failed to create snapshot '{name}' on drive '{drive}' "
                f"for VM '{vm_id}': {e}"
            )

    def load(self, vm_id: str, drive: str, name: str) -> Dict[str, Any]:
        """
        Restore/load snapshot on storage device.

        Args:
            vm_id: VM identifier (name or ID)
            drive: Storage drive name
            name: Snapshot name

        Returns:
            Operation result dictionary

        Raises:
            SnapshotCoordinatorError: If VM not found or operation fails
        """
        try:
            vm = self.state_manager.get_vm(vm_id)
            if not vm:
                raise SnapshotCoordinatorError(f"VM '{vm_id}' not found")

            # Create snapshot manager
            storage_manager = StorageManager(vm_id)
            storage_configs = vm.config_data.get("storage", [])
            if storage_configs:
                storage_manager.add_storage_from_config(storage_configs)
            snapshot_mgr = SnapshotManager(vm_id, storage_manager)

            # Load snapshot
            result = snapshot_mgr.load(drive, name)
            LOG.info(
                f"Loaded snapshot '{name}' on drive '{drive}' for VM '{vm_id}'"
            )
            return result

        except SnapshotError as e:
            raise SnapshotCoordinatorError(str(e))
        except Exception as e:
            raise SnapshotCoordinatorError(
                f"Failed to load snapshot '{name}' on drive '{drive}' "
                f"for VM '{vm_id}': {e}"
            )

    def list(self, vm_id: str, drive: str) -> List[str]:
        """
        List snapshots for VM storage device.

        Args:
            vm_id: VM identifier (name or ID)
            drive: Storage drive name

        Returns:
            List of snapshot names

        Raises:
            SnapshotCoordinatorError: If VM not found or operation fails
        """
        try:
            vm = self.state_manager.get_vm(vm_id)
            if not vm:
                raise SnapshotCoordinatorError(f"VM '{vm_id}' not found")

            # Create snapshot manager
            storage_manager = StorageManager(vm_id)
            storage_configs = vm.config_data.get("storage", [])
            if storage_configs:
                storage_manager.add_storage_from_config(storage_configs)
            snapshot_mgr = SnapshotManager(vm_id, storage_manager)

            # List snapshots
            snapshots = snapshot_mgr.list(drive)
            LOG.debug(
                f"Listed {len(snapshots)} snapshot(s) on drive '{drive}' "
                f"for VM '{vm_id}'"
            )
            return snapshots

        except SnapshotError as e:
            raise SnapshotCoordinatorError(str(e))
        except Exception as e:
            raise SnapshotCoordinatorError(
                f"Failed to list snapshots on drive '{drive}' "
                f"for VM '{vm_id}': {e}"
            )

    def get_snapshot_capable_drives(self, vm_id: str) -> List[str]:
        """
        Get list of drives that support snapshots for a VM.

        Args:
            vm_id: VM identifier (name or ID)

        Returns:
            List of drive names that support snapshots (QCOW2 only)

        Raises:
            SnapshotCoordinatorError: If VM not found
        """
        try:
            vm = self.state_manager.get_vm(vm_id)
            if not vm:
                raise SnapshotCoordinatorError(f"VM '{vm_id}' not found")

            # Create snapshot manager
            storage_manager = StorageManager(vm_id)
            storage_configs = vm.config_data.get("storage", [])
            if storage_configs:
                storage_manager.add_storage_from_config(storage_configs)
            snapshot_mgr = SnapshotManager(vm_id, storage_manager)

            # Get snapshot-capable drives
            drives = snapshot_mgr.list_snapshot_capable_drives()
            LOG.debug(
                f"Found {len(drives)} snapshot-capable drive(s) for VM '{vm_id}'"
            )
            return drives

        except Exception as e:
            raise SnapshotCoordinatorError(
                f"Failed to get snapshot-capable drives for VM '{vm_id}': {e}"
            )

    def get_drive_info(self, vm_id: str, drive: str) -> Dict[str, Any]:
        """
        Get detailed information about a storage drive including snapshots.

        Args:
            vm_id: VM identifier (name or ID)
            drive: Storage drive name

        Returns:
            Dictionary with drive information and snapshot list

        Raises:
            SnapshotCoordinatorError: If VM or drive not found
        """
        try:
            vm = self.state_manager.get_vm(vm_id)
            if not vm:
                raise SnapshotCoordinatorError(f"VM '{vm_id}' not found")

            # Create snapshot manager
            storage_manager = StorageManager(vm_id)
            storage_configs = vm.config_data.get("storage", [])
            if storage_configs:
                storage_manager.add_storage_from_config(storage_configs)
            snapshot_mgr = SnapshotManager(vm_id, storage_manager)

            # Get drive info with snapshots
            info = snapshot_mgr.get_drive_info(drive)
            return info

        except SnapshotError as e:
            raise SnapshotCoordinatorError(str(e))
        except Exception as e:
            raise SnapshotCoordinatorError(
                f"Failed to get drive info for '{drive}' on VM '{vm_id}': {e}"
            )
