# terminal.py

"""Manages TTYd processes for single (solo-server) or multi-terminal (apps-server) setups, ensuring their lifecycle, cleanup, and health monitoring."""

import os
import sys
import socket
import time
import signal
import subprocess
import platform
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI

from .exceptions import TTYDStartupError, TTYDProcessError, PortAllocationError
from .installer import setup_ttyd
from .models import TTYDConfig, ScriptConfig, IndexPageConfig
from .logger import route_color_manager
from .wrappers import create_dynamic_wrapper_file, cleanup_stale_param_files, cleanup_stale_ephemeral_files

logger = logging.getLogger("terminaide")


def find_venv_python(script_path: str) -> Optional[str]:
    """
    Find the Python executable for a virtual environment associated with the given script.
    
    Searches from the script directory upward for common virtual environment patterns:
    - .venv/bin/python (Poetry, manual venv)
    - venv/bin/python (standard venv)
    - env/bin/python (common convention)
    
    Also checks for Poetry projects (pyproject.toml + .venv).
    
    Args:
        script_path: Path to the Python script
        
    Returns:
        Path to virtual environment Python executable, or None if not found
    """
    script_path = Path(script_path).resolve()
    
    # Start from script directory and search upward
    search_dir = script_path.parent
    
    # Common venv directory names to check
    venv_names = ['.venv', 'venv', 'env']
    
    # Search up the directory tree
    for current_dir in [search_dir] + list(search_dir.parents):
        # Check for common venv directories
        for venv_name in venv_names:
            venv_path = current_dir / venv_name
            python_path = venv_path / 'bin' / 'python'
            
            if python_path.exists() and python_path.is_file():
                # Verify it's executable
                if os.access(python_path, os.X_OK):
                    return str(python_path)
        
        # Check for Poetry project (pyproject.toml + .venv)
        pyproject_path = current_dir / 'pyproject.toml'
        if pyproject_path.exists():
            poetry_venv = current_dir / '.venv' / 'bin' / 'python'
            if poetry_venv.exists() and os.access(poetry_venv, os.X_OK):
                return str(poetry_venv)
        
        # Stop at filesystem root or when we find a git repo root
        if current_dir == current_dir.parent:
            break
        
        # Stop if we find a .git directory (project root)
        if (current_dir / '.git').exists():
            break
    
    return None


def has_venv_marker(directory: Path) -> bool:
    """
    Check if a directory contains virtual environment markers.
    
    Args:
        directory: Directory to check
        
    Returns:
        True if directory appears to contain a virtual environment
    """
    venv_markers = [
        'pyvenv.cfg',  # Standard venv marker
        'bin/python',  # Unix venv structure
        'lib/python',  # Python lib directory
    ]
    
    for marker in venv_markers:
        if (directory / marker).exists():
            return True
    
    return False


class TTYDManager:
    """Manages the lifecycle of ttyd processes, including startup, shutdown, health checks, resource cleanup, and port allocation. Supports single (solo-server) or multi-terminal (apps-server) configurations."""

    def __init__(self, config: TTYDConfig, force_reinstall_ttyd: bool = None):
        """
        Initialize TTYDManager with the given TTYDConfig.

        Args:
            config: The TTYDConfig object
            force_reinstall_ttyd: If True, force reinstall ttyd even if it exists
        """
        self.config = config
        self._ttyd_path: Optional[Path] = None
        self._setup_ttyd(force_reinstall_ttyd)

        # Track processes by route
        self.processes: Dict[str, subprocess.Popen] = {}
        self.start_times: Dict[str, datetime] = {}

        # Filter to only terminal routes (ScriptConfig instances)
        self.terminal_configs: List[ScriptConfig] = [
            cfg for cfg in config.route_configs if isinstance(cfg, ScriptConfig)
        ]

        # Base port handling
        self._base_port = config.port
        self._allocate_ports()
        
        # Note: Don't clean up stale ephemeral files here as function wrappers 
        # may have already been created by serve_apps()
        
        # Generate dynamic wrappers for routes with dynamic=True
        self._generate_dynamic_wrappers()
        
        # Clean up any stale parameter files
        cleanup_stale_param_files()
        
        # Only clean up stale ephemeral script files if we don't have function-based routes
        # Function-based routes create wrapper scripts that shouldn't be deleted
        has_function_routes = any(cfg.is_function_based for cfg in self.terminal_configs)
        entry_mode = getattr(self.config, '_mode', 'script')
        
        # Never cleanup in function mode - the wrapper was just created
        if entry_mode == 'function' or has_function_routes:
            logger.debug(f"Skipping ephemeral cleanup (function mode or function routes detected)")
        else:
            cleanup_stale_ephemeral_files()

    def _setup_ttyd(self, force_reinstall: bool = None) -> None:
        """
        Set up and verify the ttyd binary.

        Args:
            force_reinstall: If True, force reinstall ttyd even if it exists
        """
        try:
            self._ttyd_path = setup_ttyd(force_reinstall)
            logger.debug("Using ttyd binary at:")
            logger.debug(f"{self._ttyd_path}")
        except Exception as e:
            logger.error(f"Failed to set up ttyd: {e}")
            raise TTYDStartupError(f"Failed to set up ttyd: {e}")

    def _allocate_ports(self) -> None:
        """
        Allocate and validate ports for each terminal configuration.
        """
        configs_to_assign = [c for c in self.terminal_configs if c.port is None]
        assigned_ports = {c.port for c in self.terminal_configs if c.port is not None}
        next_port = self._base_port

        # Track newly assigned ports
        new_assignments = []

        for cfg in configs_to_assign:
            while next_port in assigned_ports or self._is_port_in_use(
                "127.0.0.1", next_port
            ):
                next_port += 1
                if next_port > 65000:
                    raise PortAllocationError("Port range exhausted")
            cfg.port = next_port
            assigned_ports.add(next_port)
            new_assignments.append((cfg.route_path, next_port))
            next_port += 1

        # Log all port assignments in a single message
        if new_assignments:
            assignments_str = ", ".join(
                [f"{route}:{port}" for route, port in new_assignments]
            )
            logger.debug(f"Port assignments: {assignments_str}")
    
    def _generate_dynamic_wrappers(self) -> None:
        """
        Generate dynamic wrapper scripts for routes with dynamic=True.
        """
        for cfg in self.terminal_configs:
            if cfg.dynamic:
                # Skip if already has a dynamic wrapper (e.g. from reload)
                if cfg._dynamic_wrapper_path and cfg._dynamic_wrapper_path.exists():
                    continue
                
                # Get the actual script path (could be function wrapper)
                script_path = cfg._function_wrapper_path if cfg.is_function_based else cfg.script
                if not script_path:
                    logger.error(f"No script path for dynamic route {cfg.route_path}")
                    continue
                
                # Determine Python executable for the wrapper
                python_executable = sys.executable
                if self.config.venv_detection:
                    venv_python = find_venv_python(str(script_path))
                    if venv_python:
                        python_executable = venv_python
                
                # Create dynamic wrapper
                try:
                    wrapper_path = create_dynamic_wrapper_file(
                        script_path=script_path,
                        static_args=cfg.args,
                        route_path=cfg.route_path,
                        python_executable=python_executable,
                        args_param=cfg.args_param,
                    )
                    cfg.set_dynamic_wrapper_path(wrapper_path)
                    logger.debug(f"Created dynamic wrapper for route {cfg.route_path}")
                except Exception as e:
                    logger.error(f"Failed to create dynamic wrapper for route {cfg.route_path}: {e}")
                    raise TTYDStartupError(f"Failed to create dynamic wrapper: {e}")

    def _build_command(self, script_config: ScriptConfig) -> List[str]:
        """
        Construct the ttyd command using global and script-specific configs.
        """
        if not self._ttyd_path:
            raise TTYDStartupError("ttyd binary path not set")

        cmd = [str(self._ttyd_path)]
        cmd.extend(["-p", str(script_config.port)])
        cmd.extend(["-i", self.config.ttyd_options.interface])

        if not self.config.ttyd_options.check_origin:
            cmd.append("--no-check-origin")

        if self.config.ttyd_options.credential_required:
            if not (
                self.config.ttyd_options.username and self.config.ttyd_options.password
            ):
                raise TTYDStartupError("Credentials required but not provided")
            cmd.extend(
                [
                    "-c",
                    f"{self.config.ttyd_options.username}:{self.config.ttyd_options.password}",
                ]
            )

        if self.config.log_level == "debug":
            cmd.extend(["-d", "3"])

        theme_json = self.config.theme.model_dump_json()
        cmd.extend(["-t", f"theme={theme_json}"])

        cmd.extend(["-t", "cursorInactiveStyle=none"])
        # cmd.extend(['-t', 'cursorWidth=0'])
        cmd.extend(["-t", "cursorBlink=True"])

        if self.config.ttyd_options.writable:
            cmd.append("--writable")
        else:
            cmd.append("-R")

        # Use effective_script_path to get the actual script to run (direct script or function wrapper)
        script_path = script_config.effective_script_path
        if script_path is None:
            raise TTYDStartupError(
                f"Script path not set for route {script_config.route_path}"
            )

        # Find the cursor.py path
        cursor_manager_path = Path(__file__).parent / "cursor.py"

        # Check if cursor management is enabled via environment variable
        cursor_mgmt_enabled = os.environ.get("TERMINAIDE_CURSOR_MGMT", "1").lower() in (
            "1",
            "true",
            "yes",
            "enabled",
        )

        # Determine Python executable to use
        python_executable = sys.executable  # Default fallback
        
        # Try to find virtual environment Python if detection is enabled
        if self.config.venv_detection:
            venv_python = find_venv_python(str(script_path))
            if venv_python:
                python_executable = venv_python
                logger.debug(f"Found virtual environment Python: {venv_python}")
            else:
                logger.debug(f"No virtual environment found for script: {script_path}")
        
        # Use cursor manager if it exists and is enabled
        if cursor_mgmt_enabled and cursor_manager_path.exists():
            target_desc = (
                f"dynamic wrapper script"
                if script_config.dynamic
                else f"function wrapper script"
                if script_config.is_function_based
                else "script"
            )
            logger.debug(f"Using cursor manager for {target_desc}: {script_path}")
            python_cmd = [python_executable, str(cursor_manager_path), str(script_path)]
        else:
            if cursor_mgmt_enabled and not cursor_manager_path.exists():
                logger.warning(
                    f"Cursor manager not found at {cursor_manager_path}, using direct execution"
                )
            python_cmd = [python_executable, str(script_path)]

        if script_config.args:
            python_cmd.extend(script_config.args)

        cmd.extend(python_cmd)
        return cmd

    def _is_port_in_use(self, host: str, port: int) -> bool:
        """
        Check if a TCP port is in use on the given host.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)
            return sock.connect_ex((host, port)) == 0

    def _kill_process_on_port(self, host: str, port: int) -> None:
        """
        Attempt to kill any process listening on the given port, if supported.
        """
        system = platform.system().lower()
        logger.warning(f"Port {port} is in use. Attempting to kill leftover process...")

        try:
            if system in ["linux", "darwin"]:
                result = subprocess.run(
                    f"lsof -t -i tcp:{port}".split(), capture_output=True, text=True
                )
                pids = result.stdout.strip().split()
                for pid in pids:
                    if pid.isdigit():
                        logger.warning(f"Killing leftover process {pid} on port {port}")
                        subprocess.run(["kill", "-9", pid], check=False)
            else:
                logger.warning("Automatic kill not implemented on this OS.")
        except Exception as e:
            logger.error(f"Failed to kill leftover process on port {port}: {e}")

    def start(self) -> None:
        """
        Start all ttyd processes for each configured terminal script.
        """
        if not self.terminal_configs:
            logger.info("No terminal routes configured - no ttyd processes to start")
            return

        script_count = len(self.terminal_configs)
        mode_type = "apps-server" if self.config.is_multi_script else "solo-server"
        entry_mode = getattr(self.config, "_mode", "script")

        # Count function-based routes
        function_count = sum(
            1 for cfg in self.terminal_configs if cfg.is_function_based
        )

        type_info = (
            f"({function_count} function, {script_count - function_count} script)"
            if function_count > 0
            else f"({script_count} script)"
        )

        logger.debug(f"Starting {script_count} ttyd processes {type_info}")

        success_count = 0
        for script_config in self.terminal_configs:
            try:
                self.start_process(script_config)
                success_count += 1
            except Exception as e:
                logger.error(
                    f"Failed to start process for {script_config.route_path}: {e}"
                )

    def start_process(self, script_config: ScriptConfig) -> None:
        """
        Launch a single ttyd process for the given script config.
        """
        route_path = script_config.route_path
        if route_path in self.processes and self.is_process_running(route_path):
            raise TTYDProcessError(f"TTYd already running for route {route_path}")

        host = self.config.ttyd_options.interface
        port = script_config.port

        if self._is_port_in_use(host, port):
            self._kill_process_on_port(host, port)
            time.sleep(1.0)
            if self._is_port_in_use(host, port):
                raise TTYDStartupError(
                    f"Port {port} is still in use after trying to kill leftover process."
                )

        cmd = self._build_command(script_config)

        # Log detailed command at debug level only
        logger.debug(f"Process command for {route_path}: {' '.join(cmd)}")
        
        # Prepare environment variables
        env = os.environ.copy()
        if script_config.dynamic:
            # Set the route path for dynamic wrapper to identify itself
            env["TERMINAIDE_ROUTE_PATH"] = route_path
            logger.debug(f"Setting TERMINAIDE_ROUTE_PATH={route_path} for dynamic route")

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
                env=env,
            )
            self.processes[route_path] = process
            self.start_times[route_path] = datetime.now()

            timeout = 4 if self.config.log_level == "debug" else 2
            check_interval = 0.1
            checks = int(timeout / check_interval)

            for _ in range(checks):
                if process.poll() is not None:
                    stderr = process.stderr.read().decode("utf-8")
                    logger.error(
                        f"ttyd failed to start for route {route_path}: {stderr}"
                    )
                    self.processes.pop(route_path, None)
                    self.start_times.pop(route_path, None)
                    raise TTYDStartupError(stderr=stderr)

                if self.is_process_running(route_path):
                    # Standardized logging with separate lines
                    title = script_config.title or self.config.title
                    main_line, script_line = route_color_manager.format_route_info(
                        route_path, title, script_config, port=port, pid=process.pid
                    )
                    logger.info(main_line)
                    logger.info(script_line)
                    return

                time.sleep(check_interval)

            logger.error(
                f"ttyd for route {route_path} did not start within the timeout"
            )
            self.processes.pop(route_path, None)
            self.start_times.pop(route_path, None)
            raise TTYDStartupError(f"Timeout starting ttyd for route {route_path}")

        except subprocess.SubprocessError as e:
            logger.error(f"Failed to start ttyd for route {route_path}: {e}")
            raise TTYDStartupError(str(e))

    def stop(self) -> None:
        """
        Stop all running ttyd processes.
        """
        process_count = len(self.processes)
        if process_count == 0:
            logger.debug("No ttyd processes to stop")
            return

        logger.debug(f"Stopping {process_count} ttyd processes")

        for route_path in list(self.processes.keys()):
            self.stop_process(route_path, log_individual=False)

        logger.debug("All ttyd processes stopped")

    def stop_process(self, route_path: str, log_individual: bool = True) -> None:
        """
        Stop a single ttyd process for the given route.

        Args:
            route_path: The route path of the process to stop
            log_individual: Whether to log individual process stop (False when called from stop())
        """
        process = self.processes.get(route_path)
        if not process:
            return

        if log_individual:
            logger.info(f"Stopping ttyd for route {route_path}")

        try:
            if os.name == "nt":
                process.terminate()
            else:
                try:
                    pgid = os.getpgid(process.pid)
                    os.killpg(pgid, signal.SIGTERM)
                except ProcessLookupError:
                    pass

            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                if os.name == "nt":
                    process.kill()
                else:
                    try:
                        pgid = os.getpgid(process.pid)
                        os.killpg(pgid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                try:
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    pass
        except Exception as e:
            logger.warning(f"Error cleaning up process for route {route_path}: {e}")

        self.processes.pop(route_path, None)
        self.start_times.pop(route_path, None)
        
        # Clean up wrapper files if they exist
        for cfg in self.terminal_configs:
            if cfg.route_path == route_path:
                # Clean up function wrapper
                if cfg.is_function_based and cfg._function_wrapper_path:
                    try:
                        if cfg._function_wrapper_path.exists():
                            cfg._function_wrapper_path.unlink()
                            logger.debug(f"Cleaned up function wrapper for route {route_path}")
                    except Exception as e:
                        logger.warning(f"Failed to clean up function wrapper: {e}")
                
                # Clean up dynamic wrapper
                if cfg.dynamic and cfg._dynamic_wrapper_path:
                    try:
                        if cfg._dynamic_wrapper_path.exists():
                            cfg._dynamic_wrapper_path.unlink()
                            logger.debug(f"Cleaned up dynamic wrapper for route {route_path}")
                    except Exception as e:
                        logger.warning(f"Failed to clean up dynamic wrapper: {e}")
                    
                    # Also clean up any lingering parameter file
                    from .wrappers import get_params_dir, sanitize_route_path
                    sanitized_route = sanitize_route_path(route_path)
                    cache_dir = get_params_dir(self.config)
                    param_file = cache_dir / f"terminaide_params_{sanitized_route}.json"
                    if param_file.exists():
                        try:
                            param_file.unlink()
                            logger.debug(f"Cleaned up parameter file for route {route_path}")
                        except Exception:
                            pass

        if log_individual:
            logger.info(f"Stopped ttyd for route {route_path}")

    def is_process_running(self, route_path: str) -> bool:
        """
        Check if the ttyd process for a given route is running.
        """
        process = self.processes.get(route_path)
        return bool(process and process.poll() is None)

    def get_process_uptime(self, route_path: str) -> Optional[float]:
        """
        Return the uptime in seconds for the specified route's process.
        """
        if self.is_process_running(route_path) and route_path in self.start_times:
            return (datetime.now() - self.start_times[route_path]).total_seconds()
        return None

    def check_health(self) -> Dict[str, Any]:
        """
        Gather health data for all processes, including status and uptime.
        """
        processes_health = []

        # Only check terminal configs, not index pages
        for cfg in self.terminal_configs:
            route_path = cfg.route_path
            running = self.is_process_running(route_path)

            # Add info about whether this is a function-based route
            processes_health.append(
                {
                    "route_path": route_path,
                    "script": str(cfg.effective_script_path),
                    "status": "running" if running else "stopped",
                    "uptime": self.get_process_uptime(route_path),
                    "port": cfg.port,
                    "pid": self.processes.get(route_path).pid if running else None,
                    "title": cfg.title or self.config.title,
                    "is_function_based": cfg.is_function_based,
                }
            )

        # Count index pages separately
        index_page_count = sum(
            1 for cfg in self.config.route_configs if isinstance(cfg, IndexPageConfig)
        )

        # Log a compact summary of process health with function info
        running_count = sum(1 for p in processes_health if p["status"] == "running")
        function_count = sum(
            1 for p in processes_health if p.get("is_function_based", False)
        )

        if function_count > 0:
            logger.debug(
                f"Health check: {running_count}/{len(processes_health)} terminal processes running "
                f"({function_count} function-based, {len(processes_health) - function_count} script-based)"
            )
        else:
            logger.debug(
                f"Health check: {running_count}/{len(processes_health)} terminal processes running"
            )

        if index_page_count > 0:
            logger.debug(f"Index pages configured: {index_page_count}")

        entry_mode = getattr(self.config, "_mode", "script")

        return {
            "processes": processes_health,
            "ttyd_path": str(self._ttyd_path) if self._ttyd_path else None,
            "is_multi_script": self.config.is_multi_script,
            "process_count": len(self.processes),
            "terminal_count": len(self.terminal_configs),
            "index_page_count": index_page_count,
            "function_count": function_count,
            "script_count": len(processes_health) - function_count,
            "mounting": "root" if self.config.is_root_mounted else "non-root",
            "entry_mode": entry_mode,  # Add entry mode to health check
            **self.config.get_health_check_info(),
        }

    def restart_process(self, route_path: str) -> None:
        """
        Restart the ttyd process for a given route.
        """
        logger.info(f"Restarting ttyd for route {route_path}")
        script_config = None
        for cfg in self.terminal_configs:
            if cfg.route_path == route_path:
                script_config = cfg
                break
        if not script_config:
            raise TTYDStartupError(
                f"No script configuration found for route {route_path}"
            )

        self.stop_process(route_path)
        self.start_process(script_config)

    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        """
        Manage ttyd lifecycle within a FastAPI application lifespan.
        """
        try:
            self.start()
            yield
        finally:
            self.stop()
