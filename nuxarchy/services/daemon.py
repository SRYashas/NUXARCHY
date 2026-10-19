"""
NUXARCHY Root Hardware Daemon
A lightweight, high-performance background service running as root via systemd.
Listens on a local Unix domain socket (/run/nuxarchy/nuxarchy.sock).

Provides:
- Unprivileged GUI apps continuous access to live system hardware metrics.
- Instant, passwordless execution of privileged hardware writes (ACPI profiles, fan boost, RGB).
- Zero password prompts after initial system installation.
"""

import os
import sys
import json
import time
import signal
import socket
import threading
from dataclasses import asdict
from typing import Dict, Any, Optional

from nuxarchy.backend.capability import CapabilityDetector, HardwareCapabilities
from nuxarchy.backend.telemetry.system_monitor import SystemSampler, SystemSnapshot
from nuxarchy.backend.adapters.platform_profile import PlatformProfileAdapter
from nuxarchy.backend.adapters.fan_controller import FanController
from nuxarchy.backend.adapters.lighting_adapter import LightingAdapter

DEFAULT_SOCKET_DIR = "/run/nuxarchy"
DEFAULT_SOCKET_PATH = "/run/nuxarchy/nuxarchy.sock"
FALLBACK_SOCKET_PATH = "/tmp/nuxarchy.sock"


def get_socket_path() -> str:
    if os.path.exists(DEFAULT_SOCKET_DIR) or os.access("/run", os.W_OK):
        return DEFAULT_SOCKET_PATH
    return FALLBACK_SOCKET_PATH


class NuxarchyDaemon:
    def __init__(self, socket_path: Optional[str] = None, port: int = 19854):
        # Set environment flag to prevent adapters inside daemon from recursing into DaemonClient
        os.environ["NUXARCHY_DAEMON"] = "1"

        self.socket_path = socket_path or get_socket_path()
        self.port = port
        self.running = False
        self.server_socket: Optional[socket.socket] = None

        # Hardware controllers with root access
        self.detector = CapabilityDetector(simulation_mode=False)
        self.caps = self.detector.detect()
        self.sampler = SystemSampler(self.caps)
        self.profile_adapter = PlatformProfileAdapter(direct_mode=True)
        self.fan_controller = FanController(direct_mode=True)
        self.lighting_adapter = LightingAdapter(direct_mode=True)

        # Cache latest snapshot
        self.cached_snapshot: Optional[Dict[str, Any]] = None
        self._cache_lock = threading.Lock()

    def start(self):
        self.running = True

        # Ensure runtime socket directory exists
        sock_dir = os.path.dirname(self.socket_path)
        if sock_dir and not os.path.exists(sock_dir):
            try:
                os.makedirs(sock_dir, mode=0o755, exist_ok=True)
            except Exception:
                pass

        # Remove stale socket
        if os.path.exists(self.socket_path):
            try:
                os.remove(self.socket_path)
            except Exception:
                pass

        # Create Unix domain socket (or TCP fallback on Windows)
        if hasattr(socket, "AF_UNIX") and not self.socket_path.startswith("tcp://"):
            self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.server_socket.bind(self.socket_path)
            try:
                os.chmod(self.socket_path, 0o666)
            except Exception:
                pass
        else:
            # Fallback to local TCP on Windows/testing
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(("127.0.0.1", self.port))

        self.server_socket.listen(10)
        self.server_socket.settimeout(1.0)

        # Perform initial synchronous sample so cache is instantly available to clients
        try:
            initial_snap = self.sampler.sample()
            with self._cache_lock:
                self.cached_snapshot = asdict(initial_snap)
        except Exception:
            pass

        # Start background sampler thread
        sampler_thread = threading.Thread(target=self._telemetry_worker, daemon=True)
        sampler_thread.start()

        sys.stdout.write(f"[NUXARCHY-DAEMON] Listening on {self.socket_path}\n")
        sys.stdout.flush()

        while self.running:
            try:
                conn, _ = self.server_socket.accept()
                threading.Thread(target=self._handle_client, args=(conn,), daemon=True).start()
            except socket.timeout:
                continue
            except Exception:
                break

    def stop(self):
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
        if os.path.exists(self.socket_path) and hasattr(socket, "AF_UNIX"):
            try:
                os.remove(self.socket_path)
            except Exception:
                pass
        sys.stdout.write("[NUXARCHY-DAEMON] Daemon stopped cleanly.\n")
        sys.stdout.flush()

    def _telemetry_worker(self):
        """Continuously samples hardware metrics at 1000ms intervals."""
        while self.running:
            try:
                snap = self.sampler.sample()
                with self._cache_lock:
                    self.cached_snapshot = asdict(snap)
            except Exception:
                pass
            time.sleep(1.0)

    def _handle_client(self, conn: socket.socket):
        with conn:
            conn.settimeout(5.0)
            buffer = ""
            while self.running:
                try:
                    data = conn.recv(4096)
                    if not data:
                        break
                    buffer += data.decode("utf-8", errors="ignore")
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if not line:
                            continue
                        response = self._process_request(line)
                        conn.sendall((json.dumps(response) + "\n").encode("utf-8"))
                except (socket.timeout, ConnectionResetError, BrokenPipeError, ConnectionAbortedError, OSError):
                    break
                except Exception:
                    break

    def _process_request(self, line: str) -> Dict[str, Any]:
        try:
            req = json.loads(line)
        except Exception:
            return {"status": "error", "message": "Invalid JSON"}

        action = req.get("action", "")

        if action == "ping":
            return {"status": "ok", "version": "1.0.0", "daemon": True}

        elif action == "get_capabilities":
            return {"status": "ok", "capabilities": asdict(self.caps)}

        elif action == "get_snapshot":
            with self._cache_lock:
                if self.cached_snapshot:
                    return {"status": "ok", "snapshot": self.cached_snapshot}
            # Fallback to direct synchronous sample if cache empty
            snap = self.sampler.sample()
            return {"status": "ok", "snapshot": asdict(snap)}

        elif action == "set_platform_profile":
            profile = req.get("profile", "")
            success, msg = self.profile_adapter.set_profile(profile)
            return {"status": "ok" if success else "error", "message": msg}

        elif action == "set_fan_mode":
            mode = req.get("mode", "")
            success, msg = self.fan_controller.set_cooling_mode(mode)
            return {"status": "ok" if success else "error", "message": msg}

        elif action == "set_rgb_zones":
            hex_str = req.get("hex", "")
            # Direct kernel write to /sys/devices/platform/hp-wmi/rgb_zones
            rgb_path = "/sys/devices/platform/hp-wmi/rgb_zones"
            if os.path.exists(rgb_path):
                try:
                    raw_bytes = bytes.fromhex(hex_str)
                    with open(rgb_path, "wb") as f:
                        f.write(raw_bytes)
                    return {"status": "ok", "message": "RGB zones written to hp-wmi."}
                except Exception as e:
                    return {"status": "error", "message": str(e)}
            return {"status": "ok", "message": "Simulated RGB apply."}

        return {"status": "error", "message": f"Unknown action '{action}'"}


def main():
    daemon = NuxarchyDaemon()

    def handle_signal(sig, frame):
        daemon.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        daemon.start()
    except KeyboardInterrupt:
        daemon.stop()


if __name__ == "__main__":
    main()
