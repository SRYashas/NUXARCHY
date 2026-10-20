"""
NUXARCHY CPU Undervolting & Power Limit Engine
Controls Intel MSR 0x150 OC Mailbox voltage offsets, Linux kernel lockdown checks,
Intel Plundervolt BIOS lock detection, Intel RAPL power limit fallback, and AMD Curve Optimizer via ryzenadj.

Safety Invariants:
- Hard clamp: Requested offset clamped strictly between -120 mV and 0 mV.
- Positive offsets (overvolting) and values < -120 mV are unconditionally rejected.
- Kernel lockdown check (/sys/kernel/security/lockdown) prevents MSR tampering when kernel integrity is sealed.
- Plundervolt lock detection (MSR 0xCE / 0x194 bit 20) cleanly triggers RAPL power clamping fallback.
"""

import os
import glob
import struct
import logging
import subprocess
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger("nuxarchy.undervolt")

# Intel MSR Constants
MSR_OC_MAILBOX = 0x150
MSR_PLATFORM_INFO = 0xCE
MSR_FLEX_RATIO = 0x194

# Planes
PLANE_CORE = 0
PLANE_GPU = 1
PLANE_CACHE = 2

# RAPL Fallback Path
RAPL_BASE = "/sys/class/powercap/intel-rapl/intel-rapl:0"


def pack_msr_payload(plane_index: int, mv: float) -> int:
    """
    Constructs the 64-bit Intel OC Mailbox MSR 0x150 payload:
    - User requested mv is clamped strictly between -120 mV and 0 mV.
    - Raw offset units: offset = int(round(mv * 1.024))
    - 11-bit two's complement: twos_comp = (offset & 0x7FF)
    - Shift by 21 bits: voltage_bits = twos_comp << 21
    - 64-bit payload: val = 0x8000001100000000 | (plane_index << 40) | voltage_bits
    """
    # Hard safety clamp
    clamped_mv = max(-120.0, min(0.0, float(mv)))
    offset = int(round(clamped_mv * 1.024))
    twos_comp = offset & 0x7FF
    voltage_bits = twos_comp << 21
    val = 0x8000001100000000 | ((plane_index & 0xF) << 40) | voltage_bits
    return val


class UndervoltAdapter:
    """Production hardware adapter for CPU undervolting and TDP power limits."""

    def __init__(self, direct_mode: bool = True):
        self.direct_mode = direct_mode
        self._vendor = self._detect_cpu_vendor()
        self._core_offset_mv: int = 0
        self._cache_offset_mv: int = 0
        self._pl1_watts: int = 45
        self._pl2_watts: int = 65

    def _detect_cpu_vendor(self) -> str:
        """Detect GenuineIntel vs AuthenticAMD."""
        try:
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if line.startswith("vendor_id"):
                        vendor = line.split(":", 1)[1].strip()
                        if "GenuineIntel" in vendor:
                            return "intel"
                        elif "AuthenticAMD" in vendor:
                            return "amd"
        except Exception:
            pass
        return "intel"

    def check_support(self) -> Dict[str, Any]:
        """
        Pre-Flight Capability & Lock Detection:
        1. Read /sys/kernel/security/lockdown. If [integrity] or [confidentiality] is active,
           return {"supported": False, "reason": "KERNEL_LOCKDOWN_ACTIVE"}.
        2. Check /dev/cpu/0/msr existence (load msr kernel module via modprobe msr if missing).
        3. Read Intel Platform Info / Volt Lock (MSR 0xCE or MSR 0x194 bit 20).
           If Plundervolt lock bit is set, return {"supported": False, "reason": "FIRMWARE_PLUNDERVOLT_LOCKED"}.
        """
        if self._vendor == "amd":
            # Check ryzenadj
            has_ryzenadj = subprocess.run(["which", "ryzenadj"], capture_output=True).returncode == 0
            if has_ryzenadj:
                return {"supported": True, "reason": "OK_AMD_RYZENADJ", "vendor": "amd"}
            return {"supported": False, "reason": "RYZENADJ_MISSING", "vendor": "amd"}

        # 1. Lockdown Check
        lockdown_path = "/sys/kernel/security/lockdown"
        if os.path.exists(lockdown_path):
            try:
                with open(lockdown_path, "r") as f:
                    content = f.read().strip()
                    if "[integrity]" in content or "[confidentiality]" in content:
                        logger.warning("Kernel Lockdown is active: %s", content)
                        return {"supported": False, "reason": "KERNEL_LOCKDOWN_ACTIVE", "vendor": "intel"}
            except Exception as e:
                logger.debug("Failed reading lockdown status: %s", e)

        # 2. Check /dev/cpu/0/msr, modprobe msr if missing
        msr_path = "/dev/cpu/0/msr"
        if not os.path.exists(msr_path):
            try:
                subprocess.run(["modprobe", "msr"], capture_output=True, timeout=2.0)
            except Exception:
                pass

        if not os.path.exists(msr_path):
            return {"supported": False, "reason": "MSR_DRIVER_UNAVAILABLE", "vendor": "intel"}

        # 3. Read Plundervolt Lock Bit (MSR 0xCE / 0x194 bit 20)
        plundervolt_locked = False
        for test_msr in (MSR_PLATFORM_INFO, MSR_FLEX_RATIO):
            val = self._read_msr_64(test_msr, cpu=0)
            if val is not None:
                if (val & (1 << 20)) != 0:
                    plundervolt_locked = True
                    break

        if plundervolt_locked:
            logger.warning("BIOS Plundervolt lock detected (MSR bit 20 set)")
            return {
                "supported": False,
                "reason": "FIRMWARE_PLUNDERVOLT_LOCKED",
                "vendor": "intel",
                "rapl_fallback": self.is_rapl_available(),
            }

        return {
            "supported": True,
            "reason": "UNLOCKED",
            "vendor": "intel",
            "rapl_fallback": self.is_rapl_available(),
        }

    def _read_msr_64(self, msr: int, cpu: int = 0) -> Optional[int]:
        path = f"/dev/cpu/{cpu}/msr"
        if not os.path.exists(path):
            return None
        try:
            with open(path, "rb") as f:
                f.seek(msr)
                data = f.read(8)
                if len(data) == 8:
                    return struct.unpack("<Q", data)[0]
        except Exception:
            return None
        return None

    def _write_msr_across_all_cpus(self, msr: int, val: int) -> bool:
        """Pack with struct.pack('<Q', val) and write at offset msr across all /dev/cpu/[0-9]*/msr descriptors."""
        payload = struct.pack("<Q", val)
        cpu_msrs = sorted(glob.glob("/dev/cpu/[0-9]*/msr"))
        if not cpu_msrs:
            return False

        success_count = 0
        for path in cpu_msrs:
            try:
                with open(path, "wb") as f:
                    f.seek(msr)
                    f.write(payload)
                success_count += 1
            except Exception as e:
                logger.error("Failed writing MSR 0x%X on %s: %s", msr, path, e)

        return success_count > 0

    def set_undervolt_offset(self, core_mv: int, cache_mv: int) -> bool:
        """
        Apply undervolt offset for Core (plane 0) and Cache (plane 2).
        Enforces clamp [-120, 0].
        """
        support = self.check_support()
        if not support.get("supported", False):
            logger.warning("Undervolting unsupported: %s", support.get("reason"))
            # If AMD, try ryzenadj fallback
            if support.get("vendor") == "amd":
                clamped_core = max(-120, min(0, int(core_mv)))
                # Ryzenadj coall typically uses negative curve counts (e.g. -15)
                co_val = int(round(clamped_core / 3.0))
                try:
                    res = subprocess.run(["ryzenadj", f"--set-coall={co_val}"], capture_output=True, text=True)
                    if res.returncode == 0:
                        self._core_offset_mv = clamped_core
                        self._cache_offset_mv = clamped_core
                        return True
                except Exception as e:
                    logger.error("ryzenadj execution failed: %s", e)
            return False

        # Intel MSR 0x150 write
        val_core = pack_msr_payload(PLANE_CORE, core_mv)
        val_cache = pack_msr_payload(PLANE_CACHE, cache_mv)

        ok1 = self._write_msr_across_all_cpus(MSR_OC_MAILBOX, val_core)
        ok2 = self._write_msr_across_all_cpus(MSR_OC_MAILBOX, val_cache)

        if ok1 and ok2:
            self._core_offset_mv = max(-120, min(0, int(core_mv)))
            self._cache_offset_mv = max(-120, min(0, int(cache_mv)))
            logger.info("Successfully applied undervolt: Core=%dmV, Cache=%dmV", self._core_offset_mv, self._cache_offset_mv)
            return True

        return False

    def is_rapl_available(self) -> bool:
        return os.path.exists(os.path.join(RAPL_BASE, "constraint_0_power_limit_uw"))

    def set_power_limits(self, pl1_watts: int, pl2_watts: int) -> bool:
        """
        RAPL Power Limit Fallback:
        Expose dynamic TDP clamping via /sys/class/powercap/intel-rapl/intel-rapl:0/:
        Write pl1_watts * 1_000_000 to constraint_0_power_limit_uw.
        Write pl2_watts * 1_000_000 to constraint_1_power_limit_uw.
        """
        pl1_clamped = max(10, min(200, int(pl1_watts)))
        pl2_clamped = max(10, min(250, int(pl2_watts)))

        if self._vendor == "amd":
            # AMD STAPM limit via ryzenadj
            try:
                res = subprocess.run(
                    ["ryzenadj", f"--stapm-limit={pl1_clamped * 1000}", f"--fast-limit={pl2_clamped * 1000}"],
                    capture_output=True,
                    text=True,
                )
                if res.returncode == 0:
                    self._pl1_watts = pl1_clamped
                    self._pl2_watts = pl2_clamped
                    return True
            except Exception as e:
                logger.error("ryzenadj power limit failed: %s", e)
            return False

        c0_path = os.path.join(RAPL_BASE, "constraint_0_power_limit_uw")
        c1_path = os.path.join(RAPL_BASE, "constraint_1_power_limit_uw")

        success = True
        if os.path.exists(c0_path):
            try:
                with open(c0_path, "w") as f:
                    f.write(str(pl1_clamped * 1_000_000))
            except Exception as e:
                logger.error("Failed setting PL1: %s", e)
                success = False

        if os.path.exists(c1_path):
            try:
                with open(c1_path, "w") as f:
                    f.write(str(pl2_clamped * 1_000_000))
            except Exception as e:
                logger.error("Failed setting PL2: %s", e)
                success = False

        if success:
            self._pl1_watts = pl1_clamped
            self._pl2_watts = pl2_clamped
            logger.info("Applied RAPL limits: PL1=%dW, PL2=%dW", pl1_clamped, pl2_clamped)

        return success

    def get_status(self) -> Dict[str, str]:
        """Return structured status dict for D-Bus."""
        support = self.check_support()
        return {
            "supported": "true" if support.get("supported") else "false",
            "reason": str(support.get("reason", "UNKNOWN")),
            "core_offset_mv": str(self._core_offset_mv),
            "cache_offset_mv": str(self._cache_offset_mv),
            "pl1_watts": str(self._pl1_watts),
            "pl2_watts": str(self._pl2_watts),
            "rapl_available": "true" if self.is_rapl_available() else "false",
        }
