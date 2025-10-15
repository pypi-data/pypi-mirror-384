"""
Runner Client

Client for communicating with VM runner processes via Unix sockets.
Used by CLI to send commands to running VM runner processes.

Architecture:
- Each VM has unique socket path
- Client connects, sends request, receives response, disconnects
- Synchronous and async interfaces
- Error handling for connection issues
"""

import asyncio
import json
import os
import socket
from pathlib import Path
from typing import Any, Dict, Optional

from ..constants import Intervals, Retries, Timeouts
from ..logger import LOG
from .retry import async_retry_with_backoff, CircuitBreaker

# Optional dependency - imported inline with fallback
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class RunnerClientError(Exception):
    """Runner client communication errors."""


class RunnerClient:
    """
    Client for communicating with a VM runner process.

    Used by CLI to send commands to running VM runners via Unix sockets.
    Provides both synchronous and asynchronous interfaces.

    Example:
        client = RunnerClient("vm1", state_manager)
        result = client.send_command("qmp", "query-status")
    """

    def __init__(self, vm_id: str, state_manager):
        """
        Initialize runner client.

        Args:
            vm_id: VM identifier
            state_manager: StateManager instance for DB access
        """
        self.vm_id = vm_id
        self.state_manager = state_manager
        self.socket_path = self._get_socket_path()
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=5, timeout=60.0
        )

        LOG.debug(f"RunnerClient initialized for {vm_id}")

    def is_runner_running(self) -> bool:
        """
        Check if VM runner process is running.

        Uses psutil if available for accurate check, otherwise
        falls back to checking if socket exists.

        Returns:
            True if runner is running, False otherwise
        """
        # Get VM from database
        vm = self.state_manager.get_vm(self.vm_id)
        if not vm or not vm.runner_pid:
            return False

        # Check if process exists (if psutil available)
        if PSUTIL_AVAILABLE:
            return psutil.pid_exists(vm.runner_pid)
        else:
            # Fallback: check if socket exists
            return self.socket_path.exists()

    @async_retry_with_backoff(
        max_attempts=Retries.IPC_MAX_RETRIES,
        backoff_base=Intervals.IPC_BACKOFF_BASE,
        exceptions=(ConnectionRefusedError, FileNotFoundError, OSError),
    )
    async def _connect_to_socket(self):
        """
        Connect to Unix socket with retry logic.

        Internal method that handles connection with automatic retry
        on transient failures.

        Returns:
            Tuple of (reader, writer) for socket communication

        Raises:
            ConnectionRefusedError: If connection refused
            FileNotFoundError: If socket doesn't exist
            OSError: On other connection errors
        """
        return await asyncio.wait_for(
            asyncio.open_unix_connection(str(self.socket_path)),
            timeout=Timeouts.IPC_CONNECT,
        )

    async def send_command_async(
        self, method: str, *args, **kwargs
    ) -> Dict[str, Any]:
        """
        Send command to VM runner asynchronously.

        Args:
            method: Method name (e.g., "qmp", "stop", "status", "ping")
            *args: Method arguments
            **kwargs: Method keyword arguments

        Returns:
            Result dictionary from runner

        Raises:
            RunnerClientError: If runner not running or communication fails
        """
        # Check circuit breaker
        if self._circuit_breaker.is_open():
            raise RunnerClientError(
                f"Circuit breaker open for {self.vm_id}. "
                f"Too many consecutive failures. Try again later."
            )

        # Check runner running
        if not self.is_runner_running():
            raise RunnerClientError(
                f"VM runner for {self.vm_id} is not running. "
                f"Start VM first with: maqet start {self.vm_id}"
            )

        # Check socket exists
        if not self.socket_path.exists():
            raise RunnerClientError(
                f"Socket not found: {self.socket_path}. "
                f"VM runner may have crashed."
            )

        # Build request
        request = {"method": method, "args": list(args), "kwargs": kwargs}

        LOG.debug(f"Sending IPC request: method={method}")

        try:
            # Connect to Unix socket with retry logic
            reader, writer = await self._connect_to_socket()

            try:
                # Send request
                request_data = json.dumps(request).encode("utf-8")
                writer.write(request_data)
                await writer.drain()

                # Receive response (up to 1MB)
                response_data = await asyncio.wait_for(
                    reader.read(1024 * 1024), timeout=Timeouts.IPC_COMMAND
                )
                if not response_data:
                    raise RunnerClientError("Empty response from runner")

                # Parse response
                try:
                    response = json.loads(response_data.decode("utf-8"))
                except json.JSONDecodeError as e:
                    raise RunnerClientError(f"Invalid JSON response: {e}")

                # Check response status
                if response.get("status") == "error":
                    raise RunnerClientError(response.get("error", "Unknown error"))

                LOG.debug(f"IPC response received: status={response.get('status')}")

                # Record success for circuit breaker
                self._circuit_breaker.record_success()

                return response.get("result", {})

            finally:
                # Always close connection
                try:
                    writer.close()
                    await writer.wait_closed()
                except Exception as e:
                    LOG.debug(f"Error closing connection: {e}")

        except ConnectionRefusedError as e:
            self._circuit_breaker.record_failure()
            raise RunnerClientError(
                f"Connection refused. VM runner for {self.vm_id} "
                f"may have crashed or stopped. Error: {e}"
            )
        except FileNotFoundError as e:
            self._circuit_breaker.record_failure()
            raise RunnerClientError(
                f"Socket not found: {self.socket_path}. "
                f"VM runner may have exited. Error: {e}"
            )
        except asyncio.TimeoutError as e:
            self._circuit_breaker.record_failure()
            raise RunnerClientError(
                f"IPC operation timed out for {self.vm_id}. "
                f"Runner may be unresponsive. Error: {e}"
            )
        except OSError as e:
            self._circuit_breaker.record_failure()
            raise RunnerClientError(f"Communication error: {e}")
        except RunnerClientError:
            # Already a RunnerClientError, don't wrap again
            self._circuit_breaker.record_failure()
            raise
        except Exception as e:
            self._circuit_breaker.record_failure()
            raise RunnerClientError(f"Unexpected error: {e}")

    def send_command(self, method: str, *args, **kwargs) -> Dict[str, Any]:
        """
        Send command to VM runner synchronously.

        Convenience wrapper around send_command_async() for synchronous usage.

        Args:
            method: Method name (e.g., "qmp", "stop", "status", "ping")
            *args: Method arguments
            **kwargs: Method keyword arguments

        Returns:
            Result dictionary from runner

        Raises:
            RunnerClientError: If runner not running or communication fails
        """
        return asyncio.run(self.send_command_async(method, *args, **kwargs))

    def ping(self) -> bool:
        """
        Ping VM runner to check if it's responsive.

        Returns:
            True if runner responds to ping, False otherwise
        """
        try:
            result = self.send_command("ping")
            return result == "pong"
        except RunnerClientError:
            return False

    def _get_socket_path(self) -> Path:
        """
        Get Unix socket path for this VM.

        Socket location: XDG_RUNTIME_DIR/maqet/sockets/{vm_id}.sock
        Falls back to /tmp/maqet-{uid}/sockets/ if XDG_RUNTIME_DIR not available.

        Returns:
            Path to Unix socket
        """
        # Get runtime directory (prefer XDG_RUNTIME_DIR)
        runtime_dir_base = os.environ.get(
            "XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"
        )
        if not Path(runtime_dir_base).exists():
            # Fallback to /tmp
            runtime_dir_base = f"/tmp/maqet-{os.getuid()}"

        runtime_dir = Path(runtime_dir_base) / "maqet"
        socket_dir = runtime_dir / "sockets"

        return socket_dir / f"{self.vm_id}.sock"

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"RunnerClient(vm_id={self.vm_id}, socket={self.socket_path})"
