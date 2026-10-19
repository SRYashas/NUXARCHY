"""
ACPI Platform Profile Adapter
Controls system power & acoustic targets (Quiet, Balanced, Performance)
via /sys/firmware/acpi/platform_profile and power-profiles-daemon.
"""

import os
import subprocess
from typing import List, Optional, Tuple


class PlatformProfileAdapter:
    """Safely manages laptop performance profiles."""

    PROFILE_MAP = {
        "quiet": "low-power",
        "low-power": "low-power",
        "balanced": "balanced",
        "default": "balanced",
        "performance": "performance",
        "extreme": "performance",
    }

    SYSFS_PROFILE_PATH = "/sys/firmware/acpi/platform_profile"
    SYSFS_CHOICES_PATH = "/sys/firmware/acpi/platform_profile_choices"

    def __init__(self, helper_path: Optional[str] = None):
        self.helper_path = helper_path or "/usr/lib/nuxarchy/nuxarchy-hardware-helper"
        self._simulated_profile = "balanced"

    def get_supported_profiles(self) -> List[str]:
        if os.path.exists(self.SYSFS_CHOICES_PATH):
            try:
                with open(self.SYSFS_CHOICES_PATH, "r") as f:
                    return f.read().strip().split()
            except Exception:
                pass
        return ["low-power", "balanced", "performance"]

    def get_current_profile(self) -> str:
        if os.path.exists(self.SYSFS_PROFILE_PATH):
            try:
                with open(self.SYSFS_PROFILE_PATH, "r") as f:
                    return f.read().strip()
            except Exception:
                pass
        return self._simulated_profile

    def set_profile(self, target_profile: str) -> Tuple[bool, str]:
        canonical = self.PROFILE_MAP.get(target_profile.lower(), target_profile.lower())
        supported = self.get_supported_profiles()

        if canonical not in supported:
            return False, f"Profile '{canonical}' is not supported by hardware. Available: {supported}"

        # 1. Direct sysfs write if root / writable
        if os.path.exists(self.SYSFS_PROFILE_PATH) and os.access(self.SYSFS_PROFILE_PATH, os.W_OK):
            try:
                with open(self.SYSFS_PROFILE_PATH, "w") as f:
                    f.write(canonical)
                # Verify read-back
                current = self.get_current_profile()
                if current == canonical:
                    return True, f"Successfully activated '{canonical}' mode."
            except Exception as e:
                return False, f"Direct write failed: {str(e)}"

        # 2. Try power-profiles-daemon via powerprofilesctl
        try:
            res = subprocess.run(["powerprofilesctl", "set", canonical], capture_output=True, text=True, timeout=2.0)
            if res.returncode == 0:
                return True, f"Successfully set profile to '{canonical}' via power-profiles-daemon."
        except Exception:
            pass

        # 3. Try Polkit helper
        if os.path.exists(self.helper_path):
            try:
                res = subprocess.run(["pkexec", self.helper_path, "set-platform-profile", canonical], capture_output=True, text=True, timeout=5.0)
                if res.returncode == 0:
                    return True, f"Successfully applied '{canonical}' profile via Polkit."
            except Exception as e:
                return False, f"Polkit helper error: {str(e)}"

        # Simulated fallback for development testing
        self._simulated_profile = canonical
        return True, f"Set '{canonical}' profile (Simulated Mode)."
