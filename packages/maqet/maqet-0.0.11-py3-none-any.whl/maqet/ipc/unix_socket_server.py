"""
Unix Socket IPC Server

Simple Unix domain socket server for IPC between CLI and VM runner.
Uses JSON-RPC style protocol for request/response communication.

Architecture:
- Each VM runner process has its own Unix socket
- Non-blocking async I/O using asyncio
- Simple request/response pattern
- Socket cleanup on server stop
"""

import asyncio
import json
import os
import stat
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from ..constants import Timeouts
from ..logger import LOG


class UnixSocketIPCServerError(Exception):
    """Unix socket IPC server errors."""


class UnixSocketIPCServer:
    """
    Unix domain socket server for IPC between CLI and VM runner.

    Protocol: JSON-RPC style
    - Client sends: {"method": "qmp", "args": [...], "kwargs": {...}}
    - Server responds: {"status": "success", "result": ...} or
                       {"status": "error", "error": "..."}

    Socket lifecycle:
    1. Server starts, binds to socket path
    2. Accepts connections from CLI clients
    3. Reads JSON request, calls handler
    4. Writes JSON response
    5. Closes connection
    """

    def __init__(
        self, socket_path: Path, handler: Callable[[Dict[str, Any]], Dict[str, Any]]
    ):
        """
        Initialize Unix socket server.

        Args:
            socket_path: Path to Unix socket file
            handler: Async function to handle requests
                     Takes request dict, returns response dict
        """
        self.socket_path = Path(socket_path)
        self.handler = handler
        self.server: Optional[asyncio.Server] = None
        self._running = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        LOG.debug(f"UnixSocketIPCServer initialized for {socket_path}")

    async def start(self) -> None:
        """
        Start listening on Unix socket with secure permissions.

        Process:
        1. Remove existing socket if present (stale socket handling)
        2. Set restrictive umask before socket creation
        3. Create Unix socket server
        4. Verify socket permissions are secure (0600)
        5. Start accepting connections
        6. Keep server running until stop() called

        Security:
        - Socket created with 0600 permissions (user-only access)
        - Prevents local privilege escalation (CVSS 7.8)
        - Original umask restored after socket creation

        Raises:
            UnixSocketIPCServerError: If socket already in use or bind fails
        """
        # Store event loop for cross-thread communication
        self._loop = asyncio.get_running_loop()

        # Remove existing socket if present
        if self.socket_path.exists():
            # Try to connect to check if someone is using it
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_unix_connection(str(self.socket_path)),
                    timeout=Timeouts.IPC_HEALTH_CHECK,
                )
                writer.close()
                await writer.wait_closed()
                # Someone is using it
                raise UnixSocketIPCServerError(
                    f"Socket already in use: {self.socket_path}"
                )
            except (ConnectionRefusedError, FileNotFoundError, asyncio.TimeoutError):
                # Stale socket, remove it
                LOG.debug(f"Removing stale socket {self.socket_path}")
                self.socket_path.unlink()

        # Set restrictive umask before socket creation
        # This ensures only the owner can access the socket
        old_umask = os.umask(0o077)

        try:
            # Create Unix socket server
            self.server = await asyncio.start_unix_server(
                self._handle_client, path=str(self.socket_path)
            )
            self._running = True

            # Verify socket has correct permissions (0600 for socket files)
            socket_stat = self.socket_path.stat()
            expected_mode = stat.S_IRUSR | stat.S_IWUSR  # 0o600
            actual_mode = stat.S_IMODE(socket_stat.st_mode)

            if actual_mode != expected_mode:
                LOG.warning(
                    f"Socket permissions {oct(actual_mode)} differ from "
                    f"expected {oct(expected_mode)}. Attempting to fix."
                )
                os.chmod(self.socket_path, expected_mode)

            LOG.info(
                f"IPC server listening on {self.socket_path} (mode: 0600)"
            )

            # Keep server running
            async with self.server:
                await self.server.serve_forever()

        except asyncio.CancelledError:
            # Server was stopped via stop() - this is normal
            LOG.debug("IPC server cancelled (normal shutdown)")
        except Exception as e:
            raise UnixSocketIPCServerError(f"Failed to start IPC server: {e}")
        finally:
            # Restore original umask
            os.umask(old_umask)

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """
        Handle single client connection.

        Process:
        1. Read JSON request from client
        2. Parse and validate request
        3. Call handler function
        4. Write JSON response to client
        5. Close connection

        Args:
            reader: Async stream reader
            writer: Async stream writer
        """
        try:
            # Read request (up to 1MB)
            data = await reader.read(1024 * 1024)
            if not data:
                return

            # Parse JSON request
            try:
                request = json.loads(data.decode("utf-8"))
            except json.JSONDecodeError as e:
                response = {"status": "error", "error": f"Invalid JSON: {e}"}
                writer.write(json.dumps(response).encode("utf-8"))
                await writer.drain()
                return

            LOG.debug(f"IPC request: {request.get('method', 'unknown')}")

            # Call handler
            try:
                response = await self.handler(request)
            except Exception as e:
                LOG.error(f"Handler error: {e}")
                response = {"status": "error", "error": str(e)}

            # Write response
            response_data = json.dumps(response).encode("utf-8")
            writer.write(response_data)
            await writer.drain()

            LOG.debug(f"IPC response: {response.get('status', 'unknown')}")

        except Exception as e:
            LOG.error(f"Error handling client: {e}")

        finally:
            # Close connection
            try:
                writer.close()
                await writer.wait_closed()
            except Exception as e:
                LOG.debug(f"Error closing connection: {e}")

    async def stop(self) -> None:
        """
        Stop server and cleanup socket (async version).

        Process:
        1. Close server (stop accepting connections)
        2. Remove socket file

        Note: This should be called from within the same event loop as start().
        For cross-thread stopping, use stop_sync() instead.
        """
        LOG.debug("Stopping IPC server")
        self._running = False

        # Close server
        if self.server:
            self.server.close()
            await self.server.wait_closed()

        # Remove socket file
        if self.socket_path.exists():
            try:
                self.socket_path.unlink()
                LOG.debug(f"Removed socket {self.socket_path}")
            except Exception as e:
                LOG.warning(f"Failed to remove socket: {e}")

    def stop_sync(self) -> None:
        """
        Stop server from another thread (synchronous).

        This method is thread-safe and can be called from the main thread
        to stop the IPC server running in a background thread.

        Process:
        1. Mark server as stopped
        2. Close server socket (cancels serve_forever)
        3. Remove socket file from filesystem
        """
        LOG.debug("Stopping IPC server (sync)")
        self._running = False

        # Close server socket from any thread
        # This will cause serve_forever() to raise CancelledError
        if self.server:
            # Call server.close() in a thread-safe way
            if self._loop and self._loop.is_running():
                # Schedule close in the IPC server's event loop
                self._loop.call_soon_threadsafe(self.server.close)
            else:
                # Event loop not running, close directly
                self.server.close()

        # Remove socket file (filesystem operation, thread-safe)
        if self.socket_path.exists():
            try:
                self.socket_path.unlink()
                LOG.debug(f"Removed socket {self.socket_path}")
            except Exception as e:
                LOG.warning(f"Failed to remove socket: {e}")

    @property
    def is_running(self) -> bool:
        """Check if server is running."""
        return self._running
