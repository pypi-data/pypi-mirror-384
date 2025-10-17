#!/usr/bin/env python3
"""
Aria2 Python Bindings with Automatic Daemon Management
"""

import sys
import os
from typing import Optional, List, Dict, Any
import subprocess
import time
import atexit

# Import the Rust extension
try:
    from . import aria2a as _rust_module
    _PyAria2Client = _rust_module.PyAria2Client
    _PySecureDaemonManager = _rust_module.PySecureDaemonManager
except ImportError:
    # Fallback for direct import
    import aria2a as _rust_module
    _PyAria2Client = _rust_module.PyAria2Client
    _PySecureDaemonManager = _rust_module.PySecureDaemonManager


class Aria2DaemonManager:
    """Manages aria2 daemon lifecycle with security layers."""

    def __init__(self, secret: str = "aria2python", port: int = 6800):
        self.secret = secret
        self.port = port
        self.endpoint = f"http://localhost:{port}/jsonrpc"
        self._rust_manager = _PySecureDaemonManager(secret, port)

    def _find_aria2c(self) -> Optional[str]:
        """Find aria2c executable in PATH (fallback for external aria2c)."""
        import shutil
        return shutil.which("aria2c")

    def is_daemon_running(self) -> bool:
        """Check if aria2 daemon is running."""
        return self._rust_manager.is_daemon_running()

    def start_daemon(self) -> bool:
        """Start aria2 daemon with security layers."""
        try:
            self._rust_manager.start_daemon()
            return True
        except Exception as e:
            print(f"Failed to start aria2 daemon: {e}")
            return False

    def stop_daemon(self):
        """Stop aria2 daemon and cleanup."""
        try:
            self._rust_manager.stop_daemon()
        except Exception as e:
            print(f"Error stopping daemon: {e}")

    def ensure_daemon_running(self) -> bool:
        """Ensure daemon is running, start if necessary."""
        if self.is_daemon_running():
            return True
        return self.start_daemon()


class PyAria2Client:
    """
    Enhanced Aria2Client with automatic daemon management and security layers.

    If daemon is not running, it will be started automatically with security verification.
    """

    def __init__(self, endpoint: Optional[str] = None, secret: Optional[str] = None,
                 timeout_seconds: Optional[float] = None, auto_start_daemon: bool = True):
        print(f"DEBUG: Creating PyAria2Client with auto_start_daemon={auto_start_daemon}")
        self.endpoint = endpoint or "http://localhost:6800/jsonrpc"
        self.secret = secret or "aria2python"
        self.timeout_seconds = timeout_seconds
        self.daemon_manager = Aria2DaemonManager(self.secret)
        print(f"DEBUG: Daemon manager created, checking if running: {self.daemon_manager.is_daemon_running()}")

        if auto_start_daemon and not self.daemon_manager.is_daemon_running():
            print("DEBUG: Starting daemon automatically...")
            if not self.daemon_manager.start_daemon():
                print("DEBUG: Failed to start daemon")
                raise RuntimeError("Failed to start aria2 daemon automatically")
            print("DEBUG: Daemon started successfully")

        print("DEBUG: Creating Rust client")
        self._client = _PyAria2Client(self.endpoint, self.secret, self.timeout_seconds)
        print("DEBUG: PyAria2Client created successfully")

    def __getattr__(self, name):
        """Delegate all method calls to the underlying Rust client."""
        return getattr(self._client, name)


# Also export the original Rust client for advanced usage
RustAria2Client = _PyAria2Client