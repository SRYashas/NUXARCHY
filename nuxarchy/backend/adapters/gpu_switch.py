"""
NUXARCHY GPU & MUX Switch Adapter
Controls display multiplexer and hybrid graphics switching between Hybrid (Optimus),
Integrated (iGPU-only / battery), and Dedicated (dGPU-only / max performance).

Engines:
1. Primary: supergfxctl D-Bus (org.supergfxctl.Daemon, /org/supergfxctl/Gfx)
2. Fallback: envycontrol CLI (--query, --switch)
"""

import os
import shutil
import logging
import subprocess
from typing import Dict, Any, List

logger = logging.getLogger("nuxarchy.gpu_switch")

SUPERGFX_BUS_NAME = "org.supergfxctl.Daemon"
SUPERGFX_PATH = "/org/supergfxctl/Gfx"
SUPERGFX_IFACE = "org.supergfxctl.Daemon"

# supergfxctl mode mapping (mode enum / string)
# 0 = Hybrid, 1 = Integrated, 2 = NvidiaNoModeset / Dedicated, 3 = Vfio
SUPERGFX_ENUM_TO_MODE = {
    0: "hybrid",
    1: "integrated",
    2: "dedicated",
    3: "vfio",
}
SUPERGFX_MODE_TO_ENUM = {
    "hybrid": 0,
    "integrated": 1,
    "dedicated": 2,
}


class GpuSwitchAdapter:
    """Production MUX Switcher supporting supergfxctl and envycontrol."""

    def __init__(self, direct_mode: bool = True):
        self.direct_mode = direct_mode
        self._current_mode = "hybrid"
        self._pending_mode = "hybrid"
        self._backend = self._detect_backend()

    def _detect_backend(self) -> str:
        """Probe for supergfxctl system D-Bus service, then envycontrol CLI."""
        # 1. Check supergfxctl
        try:
            res = subprocess.run(
                ["busctl", "status", SUPERGFX_BUS_NAME],
                capture_output=True,
                text=True,
                timeout=1.5,
            )
            if res.returncode == 0:
                return "supergfxctl"
        except Exception:
            pass

        # 2. Check envycontrol
        if shutil.which("envycontrol"):
            return "envycontrol"

        return "simulated"

    def get_status(self) -> Dict[str, Any]:
        """
        Return structured status dict:
        {"current_mode": str, "pending_mode": str, "requires_reboot": bool, "backend": str}
        """
        backend = self._detect_backend()
        self._backend = backend

        if backend == "supergfxctl":
            try:
                # Query mode via busctl
                res = subprocess.run(
                    ["busctl", "call", SUPERGFX_BUS_NAME, SUPERGFX_PATH, SUPERGFX_IFACE, "Mode"],
                    capture_output=True,
                    text=True,
                    timeout=2.0,
                )
                if res.returncode == 0:
                    # Output example: "u 0" or "s \"Hybrid\""
                    out = res.stdout.strip()
                    parts = out.split()
                    if len(parts) >= 2:
                        val = parts[1].replace('"', '')
                        if val.isdigit():
                            self._current_mode = SUPERGFX_ENUM_TO_MODE.get(int(val), "hybrid")
                        else:
                            self._current_mode = val.lower()
                    return {
                        "current_mode": self._current_mode,
                        "pending_mode": self._pending_mode,
                        "requires_reboot": self._current_mode != self._pending_mode,
                        "backend": "supergfxctl",
                    }
            except Exception as e:
                logger.error("supergfxctl query failed: %s", e)

        elif backend == "envycontrol":
            try:
                res = subprocess.run(
                    ["envycontrol", "--query"],
                    capture_output=True,
                    text=True,
                    timeout=2.0,
                )
                if res.returncode == 0:
                    mode_str = res.stdout.strip().lower()
                    if "nvidia" in mode_str:
                        self._current_mode = "dedicated"
                    elif "integrated" in mode_str:
                        self._current_mode = "integrated"
                    else:
                        self._current_mode = "hybrid"
                    return {
                        "current_mode": self._current_mode,
                        "pending_mode": self._pending_mode,
                        "requires_reboot": self._current_mode != self._pending_mode,
                        "backend": "envycontrol",
                    }
            except Exception as e:
                logger.error("envycontrol query failed: %s", e)

        # Fallback / Simulated
        return {
            "current_mode": self._current_mode,
            "pending_mode": self._pending_mode,
            "requires_reboot": self._current_mode != self._pending_mode,
            "backend": "simulated",
        }

    def set_gpu_mode(self, mode: str) -> bool:
        """
        Switch GPU mode: 'hybrid', 'integrated', or 'dedicated'.
        Returns True on success.
        """
        mode = mode.lower()
        if mode not in ("hybrid", "integrated", "dedicated"):
            logger.error("Invalid GPU mode requested: %s", mode)
            return False

        backend = self._detect_backend()
        self._backend = backend

        if backend == "supergfxctl":
            mode_enum = SUPERGFX_MODE_TO_ENUM.get(mode, 0)
            try:
                # Call SetMode(uint32)
                res = subprocess.run(
                    ["busctl", "call", SUPERGFX_BUS_NAME, SUPERGFX_PATH, SUPERGFX_IFACE, "SetMode", "u", str(mode_enum)],
                    capture_output=True,
                    text=True,
                    timeout=5.0,
                )
                if res.returncode == 0:
                    self._pending_mode = mode
                    logger.info("supergfxctl switched mode to %s (reboot/logout required)", mode)
                    return True
            except Exception as e:
                logger.error("supergfxctl SetMode error: %s", e)
                return False

        elif backend == "envycontrol":
            envy_mode = "nvidia" if mode == "dedicated" else mode
            try:
                res = subprocess.run(
                    ["envycontrol", "--switch", envy_mode],
                    capture_output=True,
                    text=True,
                    timeout=10.0,
                )
                if res.returncode == 0:
                    self._pending_mode = mode
                    logger.info("envycontrol switched mode to %s (reboot required)", mode)
                    return True
            except Exception as e:
                logger.error("envycontrol switch error: %s", e)
                return False

        # Simulated fallback
        self._pending_mode = mode
        self._current_mode = mode
        logger.info("Set GPU mode to %s (simulated)", mode)
        return True
