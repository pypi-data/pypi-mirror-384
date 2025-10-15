"""
Integrated Snapshot Manager

Manages QCOW2 snapshots for VM storage drives using the unified storage system.
Provides create, load, and list operations for VM storage snapshots.
"""

import fcntl
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .constants import Defaults, Retries, Timeouts
from .exceptions import (
    SnapshotCreationError,
    SnapshotDeleteError,
    SnapshotError,
    SnapshotLoadError,
    SnapshotNotFoundError,
    StorageDeviceNotFoundError,
    StorageError,
)
from .logger import LOG
from .storage import BaseStorageDevice, StorageManager


class SnapshotManager:
    """
    Manages QCOW2 snapshots for VM storage drives.

    Integrates with the unified storage management system to provide
    snapshot operations on supported storage devices.

    # NOTE: Good - cleanly integrates with StorageManager abstraction instead
    # of directly manipulating storage files. Respects storage device
    # capabilities.
    #
    # TODO(architect, 2025-10-10): [PERF] Snapshot operations are synchronous and block
    # Context: All snapshot operations (create/load/list) use subprocess.run() which blocks
    # until qemu-img completes. For large disks (100GB+), this can take minutes with no
    # progress indication. Issue #7 in ARCHITECTURAL_REVIEW.md.
    #
    # Impact: CLI freezes, no way to cancel, users don't know if stuck or progressing
    #
    # Recommendation (Option 1 - Async): Use asyncio.create_subprocess_exec() for non-blocking
    # Recommendation (Option 2 - Progress): Add progress callback and timeout warnings
    #
    # Effort: Medium (3-5 days for async, 1-2 days for progress reporting)
    # Priority: High but defer to 1.1 (not critical until working with large disks)
    # See: ARCHITECTURAL_REVIEW.md Issue #7
    """

    def __init__(self, vm_id: str, storage_manager: StorageManager):
        """
        Initialize snapshot manager for a VM.

        Args:
            vm_id: VM identifier
            storage_manager: Unified storage manager instance
        """
        self.vm_id = vm_id
        self.storage_manager = storage_manager

    def create(
        self, drive_name: str, snapshot_name: str, overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        Create QCOW2 snapshot on specified drive.

        Args:
            drive_name: Name of storage drive
            snapshot_name: Name for the snapshot
            overwrite: Whether to overwrite existing snapshot

        Returns:
            Result dictionary with operation status

        Raises:
            SnapshotError: If drive not found or operation fails
        """
        try:
            device = self._get_snapshot_capable_device(drive_name)
            drive_path = self._get_device_file_path(device)

            # Check if snapshot already exists
            existing_snapshots = self._list_snapshots(drive_path)
            if snapshot_name in existing_snapshots:
                if overwrite:
                    # Delete existing snapshot first
                    self._run_qemu_img(
                        ["snapshot", str(drive_path), "-d", snapshot_name]
                    )
                else:
                    raise SnapshotCreationError(
                        f"Snapshot '{snapshot_name}' already exists on drive '{drive_name}'. "
                        f"Use --overwrite flag to replace it."
                    )

            # Create snapshot
            self._run_qemu_img(
                ["snapshot", str(drive_path), "-c", snapshot_name]
            )

            return {
                "status": "success",
                "operation": "create",
                "vm_id": self.vm_id,
                "drive": drive_name,
                "snapshot": snapshot_name,
                "overwrite": overwrite,
            }

        except SnapshotCreationError:
            # Re-raise specific errors
            raise
        except Exception as e:
            raise SnapshotCreationError(
                f"Failed to create snapshot '{snapshot_name}' on drive '{drive_name}': {e}"
            )

    def load(self, drive_name: str, snapshot_name: str) -> Dict[str, Any]:
        """
        Load/revert to QCOW2 snapshot on specified drive.

        Args:
            drive_name: Name of storage drive
            snapshot_name: Name of snapshot to load

        Returns:
            Result dictionary with operation status

        Raises:
            SnapshotError: If drive not found or operation fails
        """
        try:
            device = self._get_snapshot_capable_device(drive_name)
            drive_path = self._get_device_file_path(device)

            # Check if snapshot exists
            existing_snapshots = self._list_snapshots(drive_path)
            if snapshot_name not in existing_snapshots:
                available = ", ".join(existing_snapshots) if existing_snapshots else "none"
                raise SnapshotNotFoundError(
                    f"Snapshot '{snapshot_name}' not found on drive '{drive_name}'. "
                    f"Available snapshots: {available}"
                )

            # Apply/revert to snapshot
            self._run_qemu_img(
                ["snapshot", str(drive_path), "-a", snapshot_name]
            )

            return {
                "status": "success",
                "operation": "load",
                "vm_id": self.vm_id,
                "drive": drive_name,
                "snapshot": snapshot_name,
            }

        except SnapshotNotFoundError:
            # Re-raise specific errors
            raise
        except Exception as e:
            raise SnapshotLoadError(
                f"Failed to load snapshot '{snapshot_name}' on drive '{drive_name}': {e}"
            )

    def list(self, drive_name: str) -> List[str]:
        """
        List all available snapshots for specified drive.

        Args:
            drive_name: Name of storage drive

        Returns:
            List of snapshot names

        Raises:
            SnapshotError: If drive not found or operation fails
        """
        try:
            device = self._get_snapshot_capable_device(drive_name)
            drive_path = self._get_device_file_path(device)
            return self._list_snapshots(drive_path)

        except Exception as e:
            raise SnapshotError(
                f"Failed to list snapshots for drive '{drive_name}': {e}"
            )

    def _get_snapshot_capable_device(
        self, drive_name: str
    ) -> BaseStorageDevice:
        """
        Get storage device by name and verify it supports snapshots.

        Args:
            drive_name: Name of the drive

        Returns:
            Storage device that supports snapshots

        Raises:
            SnapshotError: If drive not found or doesn't support snapshots
        """
        device = self.storage_manager.get_device_by_name(drive_name)
        if not device:
            available_devices = [d.name for d in self.storage_manager.devices]
            raise SnapshotError(
                f"Drive '{drive_name}' not found in VM '{self.vm_id}'. "
                f"Available drives: {available_devices}"
            )

        if not device.supports_snapshots():
            raise SnapshotError(
                f"Drive '{drive_name}' (type: {device.get_type()}) "
                f"does not support snapshots. Only QCOW2 drives support snapshots."
            )

        return device

    def _get_device_file_path(self, device: BaseStorageDevice) -> Path:
        """
        Get file path from storage device.

        Args:
            device: Storage device

        Returns:
            Path to the storage file

        Raises:
            SnapshotError: If device doesn't have a file path or file doesn't exist
        """
        if not hasattr(device, "file_path"):
            raise SnapshotError(
                f"Storage device '{device.name}' doesn't have a file path"
            )

        file_path = device.file_path
        if not file_path.exists():
            raise SnapshotError(f"Storage file '{file_path}' does not exist")

        return file_path

    def _run_qemu_img(
        self,
        args: List[str],
        timeout: int = 300,
        max_retries: int = 3,
    ) -> str:
        """
        Run qemu-img command with given arguments.

        Args:
            args: List of command arguments (e.g., ["snapshot", "/path/to/file", "-c", "name"])
            timeout: Command timeout in seconds (default 5 minutes)
            max_retries: Maximum number of retry attempts for transient failures

        Returns:
            Command output

        Raises:
            SnapshotError: If command fails after all retries
        """
        # Verify qemu-img binary exists
        qemu_img_path = shutil.which("qemu-img")
        if not qemu_img_path:
            raise SnapshotError(
                "qemu-img binary not found in PATH. "
                "Please install QEMU tools."
            )

        # Build secure command list
        command = [qemu_img_path] + args

        # Extract file path from args for locking (usually args[1])
        # Example: ["snapshot", "/path/to/file.qcow2", "-c", "snap1"]
        lock_file = None
        lock_file_path = None
        if len(args) >= 2 and Path(args[1]).exists():
            file_path = Path(args[1])
            lock_file_path = (
                file_path.parent / f".{file_path.name}.snapshot.lock"
            )

        # Retry loop for transient failures
        last_error = None
        for attempt in range(max_retries):
            process = None
            try:
                # Acquire file lock to prevent concurrent snapshot operations
                if lock_file_path:
                    lock_file = open(lock_file_path, "w")
                    try:
                        fcntl.flock(
                            lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB
                        )
                    except BlockingIOError:
                        raise SnapshotError(
                            f"Another snapshot operation is in progress on {args[1]}. "
                            f"Please wait for it to complete."
                        )

                LOG.debug(f"Running qemu-img command: {' '.join(command)}")

                # Use Popen for better process control (kill on timeout)
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )

                try:
                    stdout, stderr = process.communicate(timeout=timeout)
                except subprocess.TimeoutExpired:
                    # Kill the process on timeout to prevent resource leaks
                    LOG.warning(
                        f"qemu-img command timed out after {timeout}s, killing process"
                    )
                    process.kill()
                    # Wait for process to actually die and collect zombie
                    try:
                        process.wait(timeout=Timeouts.PROCESS_KILL)
                    except subprocess.TimeoutExpired:
                        # Force kill if still alive
                        process.terminate()
                        process.wait(timeout=Timeouts.PROCESS_WAIT_AFTER_KILL)

                    raise SnapshotError(
                        f"qemu-img command timed out after {timeout} seconds and was killed"
                    )

                # Check exit code
                if process.returncode != 0:
                    raise subprocess.CalledProcessError(
                        process.returncode, command, stdout, stderr
                    )

                return stdout.strip()

            except subprocess.CalledProcessError as e:
                last_error = e
                # Check if error is potentially transient
                if self._is_transient_error(e.stderr):
                    if attempt < max_retries - 1:
                        wait_time = 2**attempt  # Exponential backoff
                        LOG.warning(
                            f"qemu-img command failed (attempt {attempt + 1}/{max_retries}), "
                            f"retrying in {wait_time}s: {e.stderr}"
                        )
                        time.sleep(wait_time)
                        continue
                # Non-transient error or final retry
                raise SnapshotError(
                    f"qemu-img command failed: {e.stderr.strip()}"
                )

            finally:
                # Release lock and clean up
                if lock_file:
                    try:
                        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                        lock_file.close()
                        if lock_file_path and lock_file_path.exists():
                            lock_file_path.unlink()
                    except Exception:
                        pass  # Best effort cleanup

        # Should not reach here, but handle gracefully
        if last_error:
            raise SnapshotError(
                f"qemu-img command failed after {max_retries} attempts: "
                f"{last_error.stderr.strip()}"
            )
        raise SnapshotError("qemu-img command failed for unknown reason")

    def _is_transient_error(self, stderr: str) -> bool:
        """
        Check if error message indicates a transient failure.

        Args:
            stderr: Error output from qemu-img

        Returns:
            True if error appears transient and worth retrying
        """
        transient_indicators = [
            "resource temporarily unavailable",
            "device or resource busy",
            "try again",
            "temporary failure",
            "connection timed out",
        ]
        stderr_lower = stderr.lower()
        return any(
            indicator in stderr_lower for indicator in transient_indicators
        )

    def _list_snapshots(self, drive_path: Path) -> List[str]:
        """
        List snapshots for a QCOW2 drive.

        Args:
            drive_path: Path to the drive file

        Returns:
            List of snapshot names
        """
        try:
            output = self._run_qemu_img(["snapshot", str(drive_path), "-l"])

            # Parse qemu-img snapshot output
            # Format: "Snapshot list:\nID TAG VM SIZE DATE VM CLOCK\n1 snap1 0
            # B 2024-01-01 12:00:00 00:00:00.000\n"
            lines = output.split("\n")
            snapshots = []

            for line in lines[2:]:  # Skip header lines
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        snapshot_name = parts[1]  # TAG column
                        snapshots.append(snapshot_name)

            return snapshots
        except SnapshotError:
            # If snapshot listing fails, assume no snapshots exist
            return []

    def get_drive_info(self, drive_name: str) -> Dict[str, Any]:
        """
        Get information about a storage drive including snapshot data.

        Args:
            drive_name: Name of the drive

        Returns:
            Dictionary with drive information including snapshots

        Raises:
            SnapshotError: If drive not found
        """
        device = self._get_snapshot_capable_device(drive_name)
        drive_path = self._get_device_file_path(device)
        snapshots = self._list_snapshots(drive_path)

        # Get base device info and add snapshot information
        info = device.get_info()
        info.update(
            {
                "snapshots": snapshots,
                "snapshot_count": len(snapshots),
            }
        )

        return info

    def list_snapshot_capable_drives(self) -> List[str]:
        """
        Get list of drives that support snapshots.

        Returns:
            List of drive names that support snapshots
        """
        return [
            device.name
            for device in self.storage_manager.get_snapshot_capable_devices()
        ]
