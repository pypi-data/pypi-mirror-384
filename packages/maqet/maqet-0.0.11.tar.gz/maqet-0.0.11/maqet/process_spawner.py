"""
Process Spawner

Utilities for spawning and managing detached VM runner processes.
Used by CLI to create independent VM runner processes that survive parent exit.

Architecture:
- Each VM gets its own persistent Python process (VM runner)
- Spawned processes are detached (new session, own process group)
- Processes redirect stdout/stderr to log files
- Socket-based readiness checking with timeout
- Health checks using psutil or fallback methods

Key Functions:
- spawn_vm_runner(): Create detached VM runner process
- wait_for_vm_ready(): Wait for VM runner to be ready (socket available)
- get_socket_path(): Get Unix socket path for VM
- get_log_path(): Get log file path for VM runner
- is_runner_alive(): Check if runner process is alive
"""

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

from .constants import Intervals, Timeouts
from .exceptions import ProcessNotFoundError, RunnerSpawnError
from .logger import LOG

# Optional dependency - imported inline with fallback
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Legacy exception alias (backward compatibility)
ProcessSpawnerError = RunnerSpawnError


def spawn_vm_runner(
    vm_id: str,
    db_path: Optional[Path] = None,
    timeout: int = Timeouts.PROCESS_SPAWN
) -> int:
    """
    Spawn a detached VM runner process.

    The spawned process:
    - Runs in background (detached from CLI)
    - Has its own process group (start_new_session=True)
    - Redirects stdout/stderr to log files
    - Survives parent CLI process exit
    - Returns immediately (non-blocking)

    Args:
        vm_id: VM identifier
        db_path: Optional path to database (for testing)
        timeout: Maximum time to wait for process to start (seconds)

    Returns:
        runner_pid: PID of spawned runner process

    Raises:
        ProcessSpawnerError: If spawn fails or process dies immediately

    Example:
        runner_pid = spawn_vm_runner("vm1")
        # Returns: PID of spawned runner process
    """
    # Get Python interpreter path (same interpreter as CLI)
    python_exe = sys.executable

    # Build command: python3 -m maqet.vm_runner <vm_id> [db_path]
    cmd = [python_exe, "-m", "maqet.vm_runner", vm_id]
    if db_path:
        cmd.append(str(db_path))

    # Get log file path for stdout/stderr
    log_path = get_log_path(vm_id)

    LOG.debug(f"Spawning VM runner for {vm_id}: {' '.join(cmd)}")
    LOG.debug(f"Log output: {log_path}")

    try:
        # Open log file for output
        log_file = open(log_path, "w")

        # Spawn detached process
        process = subprocess.Popen(
            cmd,
            start_new_session=True,  # Detach from parent process group
            stdin=subprocess.DEVNULL,  # No stdin (non-interactive)
            stdout=log_file,  # Redirect stdout to log
            stderr=subprocess.STDOUT,  # Redirect stderr to stdout (combined log)
            close_fds=True,  # Close all file descriptors
        )

        runner_pid = process.pid
        LOG.info(f"VM runner spawned: PID {runner_pid}")

        # Wait briefly to ensure process started successfully
        time.sleep(Intervals.PROCESS_STARTUP_WAIT)

        # Check if process still alive (didn't crash immediately)
        if process.poll() is not None:
            # Process exited immediately - read log for error
            log_file.close()
            try:
                with open(log_path, "r") as f:
                    error_output = f.read().strip()
            except Exception:
                error_output = "(could not read log)"

            raise RunnerSpawnError(
                f"VM runner '{vm_id}' failed to start (exit code {process.poll()}). "
                f"Error: {error_output}. Check log at: {log_path}"
            )

        # Close log file handle (process has its own handle now)
        log_file.close()

        return runner_pid

    except RunnerSpawnError:
        # Re-raise RunnerSpawnError as-is (don't wrap it again)
        raise
    except FileNotFoundError:
        raise RunnerSpawnError(
            f"Python interpreter not found: {python_exe}. "
            f"This should never happen - check sys.executable."
        )
    except PermissionError as e:
        raise RunnerSpawnError(
            f"Permission denied when spawning VM runner '{vm_id}': {e}. "
            f"Check file permissions for log directory."
        )
    except Exception as e:
        raise RunnerSpawnError(
            f"Failed to spawn VM runner '{vm_id}': {e}"
        )


def wait_for_vm_ready(
    vm_id: str,
    socket_path: Optional[Path] = None,
    timeout: int = Timeouts.VM_START
) -> bool:
    """
    Wait for VM runner to be ready (socket available and connectable).

    Polls for socket existence and connectivity with exponential backoff.
    Uses direct socket connection to verify socket is functional.

    Args:
        vm_id: VM identifier
        socket_path: Optional socket path (auto-detected if not provided)
        timeout: Maximum wait time in seconds

    Returns:
        True if ready within timeout, False if timeout

    Implementation Notes:
    - Polls every 0.1s initially, increasing to 0.5s
    - Checks socket exists AND is connectable
    - Uses direct socket connection for connectivity check
    - Logs progress at DEBUG level

    Example:
        socket_path = get_socket_path("vm1")
        ready = wait_for_vm_ready("vm1", socket_path, timeout=10)
        # Returns: True if ready, False if timeout
    """
    if socket_path is None:
        socket_path = get_socket_path(vm_id)

    start_time = time.time()
    poll_interval = 0.1  # Start with 100ms
    max_poll_interval = 0.5  # Cap at 500ms

    LOG.debug(f"Waiting for VM runner to be ready: {socket_path}")

    while time.time() - start_time < timeout:
        # Check if socket exists
        if socket_path.exists():
            # Socket exists, try to connect directly
            try:
                import socket as sock_module
                import json

                client_socket = sock_module.socket(sock_module.AF_UNIX, sock_module.SOCK_STREAM)
                client_socket.settimeout(2.0)
                client_socket.connect(str(socket_path))

                # Send ping request
                request = json.dumps({"method": "ping", "args": [], "kwargs": {}})
                client_socket.sendall(request.encode("utf-8"))

                # Receive response
                response_data = client_socket.recv(1024)
                response = json.loads(response_data.decode("utf-8"))

                client_socket.close()

                if response.get("status") == "success" and response.get("result") == "pong":
                    LOG.debug("VM runner ready (socket connectable)")
                    return True
                else:
                    LOG.debug("Socket exists but ping failed, retrying...")

            except (ConnectionRefusedError, FileNotFoundError, sock_module.timeout) as e:
                LOG.debug(f"Socket exists but not ready yet: {type(e).__name__}")
            except Exception as e:
                LOG.debug(f"Socket check error: {e}")

        # Sleep with exponential backoff
        time.sleep(poll_interval)
        poll_interval = min(poll_interval * 1.2, max_poll_interval)

        # Log progress every 5 seconds
        elapsed = time.time() - start_time
        if int(elapsed) % 5 == 0 and elapsed > 0:
            LOG.debug(f"Still waiting for VM runner... ({int(elapsed)}s elapsed)")

    # Timeout
    LOG.warning(f"Timeout waiting for VM runner after {timeout}s")
    return False


def get_socket_path(vm_id: str) -> Path:
    """
    Get Unix socket path for VM runner.

    Socket location: XDG_RUNTIME_DIR/maqet/sockets/{vm_id}.sock
    Falls back to /tmp/maqet-{uid}/sockets/ if XDG_RUNTIME_DIR not available.

    This MUST match the socket path used in vm_runner.py!

    Args:
        vm_id: VM identifier

    Returns:
        Path to Unix socket

    Example:
        socket_path = get_socket_path("vm1")
        # Returns: /run/user/1000/maqet/sockets/vm1.sock
    """
    # Get runtime directory (prefer XDG_RUNTIME_DIR)
    runtime_dir_base = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")

    if not Path(runtime_dir_base).exists():
        # Fallback to /tmp (already includes maqet-{uid})
        socket_dir = Path(f"/tmp/maqet-{os.getuid()}") / "sockets"
    else:
        # XDG_RUNTIME_DIR exists (e.g., /run/user/1000)
        socket_dir = Path(runtime_dir_base) / "maqet" / "sockets"

    return socket_dir / f"{vm_id}.sock"


def get_log_path(vm_id: str) -> Path:
    """
    Get log file path for VM runner.

    Log location: ~/.local/share/maqet/logs/vm_{vm_id}.log
    Creates parent directory if it doesn't exist.

    Args:
        vm_id: VM identifier

    Returns:
        Path to log file

    Example:
        log_path = get_log_path("vm1")
        # Returns: /home/user/.local/share/maqet/logs/vm_vm1.log
    """
    # Get XDG data directory
    xdg_data_home = os.environ.get(
        "XDG_DATA_HOME", os.path.expanduser("~/.local/share")
    )
    data_dir = Path(xdg_data_home) / "maqet"
    log_dir = data_dir / "logs"

    # Create directory if it doesn't exist
    log_dir.mkdir(parents=True, exist_ok=True)

    return log_dir / f"vm_{vm_id}.log"


def is_runner_alive(runner_pid: int) -> bool:
    """
    Check if runner process is alive.

    Uses psutil if available for accurate check, otherwise falls back
    to os.kill(pid, 0) which only checks if process exists.

    Args:
        runner_pid: PID of runner process

    Returns:
        True if process exists and belongs to current user, False otherwise

    Example:
        alive = is_runner_alive(12345)
        # Returns: True if process exists, False otherwise
    """
    if runner_pid is None or runner_pid <= 0:
        return False

    if PSUTIL_AVAILABLE:
        # Use psutil for accurate check
        try:
            process = psutil.Process(runner_pid)
            # Check if process exists and is not a zombie
            return process.is_running() and process.status() != psutil.STATUS_ZOMBIE
        except psutil.NoSuchProcess:
            return False
        except psutil.AccessDenied:
            # Process exists but we can't access it (different user)
            return False

    else:
        # Fallback: Check /proc/{pid}/stat for zombie status
        try:
            # First check if process exists
            os.kill(runner_pid, 0)

            # Read process status from /proc
            try:
                with open(f"/proc/{runner_pid}/stat", "r") as f:
                    stat = f.read()
                    # Process state is the 3rd field (after PID and command name in parens)
                    # States: R (running), S (sleeping), D (disk sleep), Z (zombie), T (stopped)
                    # Extract state: it's the character after the closing paren and space
                    state_start = stat.rfind(")") + 2
                    state = stat[state_start] if state_start < len(stat) else "?"
                    # Zombie state is 'Z'
                    return state != "Z"
            except (FileNotFoundError, IOError):
                # /proc not available or process gone - assume not alive
                return False

        except ProcessLookupError:
            # Process doesn't exist
            return False
        except PermissionError:
            # Process exists but different user (shouldn't happen for our processes)
            return False
        except Exception:
            return False


def kill_runner(runner_pid: int, force: bool = False) -> bool:
    """
    Kill VM runner process.

    Args:
        runner_pid: PID of runner process
        force: If True, use SIGKILL. If False, use SIGTERM (graceful)

    Returns:
        True if process was killed, False if process not found

    Example:
        # Graceful shutdown
        kill_runner(12345, force=False)

        # Force kill
        kill_runner(12345, force=True)
    """
    if not is_runner_alive(runner_pid):
        return False

    try:
        if force:
            LOG.debug(f"Force killing runner process {runner_pid} (SIGKILL)")
            os.kill(runner_pid, 9)  # SIGKILL
        else:
            LOG.debug(f"Gracefully stopping runner process {runner_pid} (SIGTERM)")
            os.kill(runner_pid, 15)  # SIGTERM
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        LOG.error(f"Permission denied when killing process {runner_pid}")
        return False
    except Exception as e:
        LOG.error(f"Failed to kill process {runner_pid}: {e}")
        return False
