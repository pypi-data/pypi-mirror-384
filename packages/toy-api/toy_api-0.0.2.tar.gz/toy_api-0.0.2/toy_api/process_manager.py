"""

Process Manager for Toy API

Manages background toy API server processes with start/stop tracking.

License: BSD 3-Clause

"""
#
# IMPORTS
#
import json
import os
import signal
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


#
# CONSTANTS
#
PIDFILE_DIR = Path(".toy_api")
PIDFILE_PATH = PIDFILE_DIR / "processes.json"


#
# PUBLIC
#
def start_background_process(config_name: str, host: str, port: int) -> Tuple[bool, str]:
    """Start a toy API server in the background.

    Args:
        config_name: Name of the config (e.g., "basic", "versioned_remote/0.1").
        host: Host to bind to.
        port: Port to bind to.

    Returns:
        Tuple of (success, message).
    """
    # Ensure pidfile directory exists
    PIDFILE_DIR.mkdir(parents=True, exist_ok=True)

    # Check if already running
    processes = _load_processes()
    if config_name in processes:
        pid = processes[config_name]["pid"]
        if _is_process_running(pid):
            return (False, f"Process already running for '{config_name}' (PID: {pid})")

    # Start process in background
    try:
        # Sanitize config name for filesystem (replace / with _)
        safe_config_name = config_name.replace('/', '_')
        log_file = PIDFILE_DIR / f"{safe_config_name}.log"

        cmd = [
            sys.executable, "-m", "toy_api.cli", "start", config_name,
            "--host", host, "--port", str(port)
        ]

        with open(log_file, 'w') as log:
            process = subprocess.Popen(
                cmd,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True
            )

        # Store process info
        processes[config_name] = {
            "pid": process.pid,
            "host": host,
            "port": port,
            "log_file": str(log_file)
        }
        _save_processes(processes)

        return (True, f"Started {config_name} on {host}:{port} (PID: {process.pid}, Log: {log_file})")

    except Exception as e:
        return (False, f"Failed to start process: {e}")


def stop_process(config_name: str) -> Tuple[bool, str]:
    """Stop a running toy API server.

    Args:
        config_name: Name of the config.

    Returns:
        Tuple of (success, message).
    """
    processes = _load_processes()

    if config_name not in processes:
        return (False, f"No process found for '{config_name}'")

    process_info = processes[config_name]
    pid = process_info["pid"]

    if not _is_process_running(pid):
        # Clean up stale entry
        del processes[config_name]
        _save_processes(processes)
        return (False, f"Process for '{config_name}' is not running (cleaned up stale entry)")

    # Try to stop the process
    try:
        os.kill(pid, signal.SIGTERM)
        del processes[config_name]
        _save_processes(processes)
        return (True, f"Stopped {config_name} (PID: {pid})")
    except Exception as e:
        return (False, f"Failed to stop process: {e}")


def stop_all_processes() -> List[Tuple[str, bool, str]]:
    """Stop all running toy API servers.

    Returns:
        List of (config_name, success, message) tuples.
    """
    processes = _load_processes()
    results = []

    for config_name in list(processes.keys()):
        success, message = stop_process(config_name)
        results.append((config_name, success, message))

    return results


def list_processes() -> Dict[str, Dict[str, Any]]:
    """List all tracked processes.

    Returns:
        Dictionary mapping config names to process info.
    """
    processes = _load_processes()

    # Clean up stale entries
    stale = []
    for config_name, info in processes.items():
        if not _is_process_running(info["pid"]):
            stale.append(config_name)

    for config_name in stale:
        del processes[config_name]

    if stale:
        _save_processes(processes)

    return processes


def get_all_configs_in_directory(directory: Optional[str] = None) -> List[Tuple[str, str]]:
    """Get all config files in a directory (including versioned subdirectories).

    Args:
        directory: Directory to search. If None, searches toy_api_config/apis/.

    Returns:
        List of (config_name, config_path) tuples.
    """
    if directory is None:
        directory = "toy_api_config/apis"

    base_path = Path(directory)
    if not base_path.exists():
        return []

    configs = []

    # Find all .yaml files recursively in apis directory
    for yaml_file in base_path.rglob("*.yaml"):
        # Get relative path from base
        rel_path = yaml_file.relative_to(base_path)

        # Create config name from path (e.g., "versioned_remote/0.1" or "basic")
        if len(rel_path.parts) > 1:
            # Versioned: parent_dir/filename (without .yaml)
            config_name = str(rel_path.parent / rel_path.stem)
        else:
            # Non-versioned: just filename (without .yaml)
            config_name = rel_path.stem

        configs.append((config_name, str(yaml_file)))

    return sorted(configs)


#
# INTERNAL
#
def _load_processes() -> Dict[str, Dict[str, Any]]:
    """Load process info from pidfile.

    Returns:
        Dictionary mapping config names to process info.
    """
    if not PIDFILE_PATH.exists():
        return {}

    try:
        with open(PIDFILE_PATH, 'r') as f:
            return json.load(f)
    except Exception:
        return {}


def _save_processes(processes: Dict[str, Dict[str, Any]]) -> None:
    """Save process info to pidfile.

    Args:
        processes: Dictionary mapping config names to process info.
    """
    PIDFILE_DIR.mkdir(parents=True, exist_ok=True)

    with open(PIDFILE_PATH, 'w') as f:
        json.dump(processes, f, indent=2)


def _is_process_running(pid: int) -> bool:
    """Check if a process is running.

    Args:
        pid: Process ID.

    Returns:
        True if process is running, False otherwise.
    """
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False
