"""
NUXARCHY Daemon Client
Allows the unprivileged GUI application to communicate with the root nuxarchy-daemon
via Unix domain socket (/run/nuxarchy/nuxarchy.sock).
"""

import os
import sys
import json
import socket
from typing import Optional, Tuple, Dict, Any

from nuxarchy.backend.capability import HardwareCapabilities
from nuxarchy.backend.telemetry.system_monitor import SystemSnapshot
from nuxarchy.backend.telemetry.cpu_monitor import CpuTelemetry
from nuxarchy.backend.telemetry.gpu_amd_monitor import AmdGpuTelemetry
from nuxarchy.backend.telemetry.gpu_nvidia_monitor import NvidiaGpuTelemetry
from nuxarchy.backend.telemetry.memory_monitor import MemoryTelemetry
from nuxarchy.backend.telemetry.network_monitor import NetworkTelemetry

DEFAULT_SOCKET_PATHS = [
    "/run/nuxarchy/nuxarchy.sock",
    "/tmp/nuxarchy.sock"
]


class DaemonClient:
    """Client for interacting with the privileged NUXARCHY root daemon."""

    _instance: Optional["DaemonClient"] = None

    @classmethod
    def instance(cls) -> "DaemonClient":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, socket_path: Optional[str] = None, tcp_port: Optional[int] = 19854):
        self.socket_path = socket_path or self._find_socket_path()
        self.tcp_port = tcp_port

    def _find_socket_path(self) -> str:
        for p in DEFAULT_SOCKET_PATHS:
            if os.path.exists(p):
                return p
        return DEFAULT_SOCKET_PATHS[0]

    def is_connected(self) -> bool:
        """Checks if the nuxarchy-daemon is actively running and responding."""
        res = self._send_request({"action": "ping"})
        return res is not None and res.get("status") == "ok"

    def _send_request(self, req: Dict[str, Any], timeout: float = 4.0) -> Optional[Dict[str, Any]]:
        sock = None
        try:
            if hasattr(socket, "AF_UNIX") and os.path.exists(self.socket_path):
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                sock.connect(self.socket_path)
            elif self.tcp_port is not None:
                # Windows / local testing TCP fallback
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                sock.connect(("127.0.0.1", self.tcp_port))
            else:
                return None

            req_bytes = (json.dumps(req) + "\n").encode("utf-8")
            sock.sendall(req_bytes)

            buffer = ""
            while "\n" not in buffer:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                buffer += chunk.decode("utf-8", errors="ignore")

            line = buffer.split("\n", 1)[0].strip()
            if line:
                return json.loads(line)
        except Exception:
            return None
        finally:
            if sock:
                try:
                    sock.close()
                except Exception:
                    pass
        return None

    def get_capabilities(self) -> Optional[HardwareCapabilities]:
        res = self._send_request({"action": "get_capabilities"})
        if res and res.get("status") == "ok":
            caps_data = res.get("capabilities", {})
            valid_keys = {f.name for f in HardwareCapabilities.__dataclass_fields__.values()}
            filtered = {k: v for k, v in caps_data.items() if k in valid_keys}
            return HardwareCapabilities(**filtered)
        return None

    def get_snapshot(self) -> Optional[SystemSnapshot]:
        res = self._send_request({"action": "get_snapshot"})
        if res and res.get("status") == "ok":
            snap_data = res.get("snapshot", {})
            snap = SystemSnapshot(
                timestamp=snap_data.get("timestamp", 0.0),
                fan_rpm=snap_data.get("fan_rpm"),
                fan_mode=snap_data.get("fan_mode", "Auto"),
                platform_profile=snap_data.get("platform_profile", "balanced"),
                battery_percent=snap_data.get("battery_percent"),
                is_ac_connected=snap_data.get("is_ac_connected", True),
            )
            if snap_data.get("cpu"):
                snap.cpu = CpuTelemetry(**{k: v for k, v in snap_data["cpu"].items() if k in CpuTelemetry.__dataclass_fields__})
            if snap_data.get("gpu_amd"):
                snap.gpu_amd = AmdGpuTelemetry(**{k: v for k, v in snap_data["gpu_amd"].items() if k in AmdGpuTelemetry.__dataclass_fields__})
            if snap_data.get("gpu_nvidia"):
                snap.gpu_nvidia = NvidiaGpuTelemetry(**{k: v for k, v in snap_data["gpu_nvidia"].items() if k in NvidiaGpuTelemetry.__dataclass_fields__})
            if snap_data.get("memory"):
                snap.memory = MemoryTelemetry(**{k: v for k, v in snap_data["memory"].items() if k in MemoryTelemetry.__dataclass_fields__})
            if snap_data.get("network"):
                snap.network = NetworkTelemetry(**{k: v for k, v in snap_data["network"].items() if k in NetworkTelemetry.__dataclass_fields__})
            return snap
        return None

    def set_platform_profile(self, profile: str) -> Tuple[bool, str]:
        res = self._send_request({"action": "set_platform_profile", "profile": profile})
        if res:
            return (res.get("status") == "ok"), res.get("message", "")
        return False, "Daemon unreachable"

    def set_fan_mode(self, mode: str) -> Tuple[bool, str]:
        res = self._send_request({"action": "set_fan_mode", "mode": mode})
        if res:
            return (res.get("status") == "ok"), res.get("message", "")
        return False, "Daemon unreachable"

    def set_rgb_zones(self, hex_str: str) -> Tuple[bool, str]:
        res = self._send_request({"action": "set_rgb_zones", "hex": hex_str})
        if res:
            return (res.get("status") == "ok"), res.get("message", "")
        return False, "Daemon unreachable"
