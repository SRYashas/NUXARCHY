#!/usr/bin/env python3
"""
OMEN Hardware Helper (Privileged Backend)
Executed via Polkit (pkexec) to perform narrowly scoped hardware adjustments:
1. set-platform-profile <low-power|balanced|performance>
2. set-fan-mode <auto|max>
3. set-keyboard-colors <24-char hex string>
"""

import sys
import os
import re

ALLOWED_PROFILES = ["low-power", "balanced", "performance"]
ALLOWED_FAN_MODES = ["auto", "max"]
PLATFORM_PROFILE_PATH = "/sys/firmware/acpi/platform_profile"
HP_WMI_MAX_FAN_PATH = "/sys/devices/platform/hp-wmi/max_fan"
HP_WMI_RGB_PATH = "/sys/devices/platform/hp-wmi/rgb_zones"


def log_audit(msg: str):
    sys.stderr.write(f"[NUXARCHY-HELPER] {msg}\n")


def set_platform_profile(profile: str) -> int:
    profile = profile.strip().lower()
    if profile not in ALLOWED_PROFILES:
        log_audit(f"REJECTED: Invalid profile '{profile}'. Allowed: {ALLOWED_PROFILES}")
        return 1

    if not os.path.exists(PLATFORM_PROFILE_PATH):
        log_audit(f"ERROR: {PLATFORM_PROFILE_PATH} does not exist on this system.")
        return 2

    try:
        with open(PLATFORM_PROFILE_PATH, "w") as f:
            f.write(profile)
        log_audit(f"SUCCESS: Platform profile set to '{profile}'.")
        return 0
    except Exception as e:
        log_audit(f"ERROR: Failed writing to {PLATFORM_PROFILE_PATH}: {str(e)}")
        return 3


def set_fan_mode(mode: str) -> int:
    mode = mode.strip().lower()
    if mode not in ALLOWED_FAN_MODES:
        log_audit(f"REJECTED: Invalid fan mode '{mode}'. Allowed: {ALLOWED_FAN_MODES}")
        return 1

    val = "1" if mode == "max" else "0"
    if os.path.exists(HP_WMI_MAX_FAN_PATH):
        try:
            with open(HP_WMI_MAX_FAN_PATH, "w") as f:
                f.write(val)
            log_audit(f"SUCCESS: Max fan set to {val}.")
            return 0
        except Exception as e:
            log_audit(f"ERROR: Failed writing to {HP_WMI_MAX_FAN_PATH}: {str(e)}")
            return 3
    else:
        log_audit("NOTICE: hp-wmi max_fan sysfs node not present on this hardware.")
        return 0


def set_keyboard_colors(hex_string: str) -> int:
    hex_string = hex_string.strip().lower()
    # 4 zones * 3 bytes (R, G, B) = 12 bytes = 24 hex characters
    if not re.match(r"^[0-9a-f]{24}$", hex_string):
        log_audit("REJECTED: Invalid hex color payload. Expected 24 hex characters.")
        return 1

    if os.path.exists(HP_WMI_RGB_PATH):
        try:
            raw_bytes = bytes.fromhex(hex_string)
            with open(HP_WMI_RGB_PATH, "wb") as f:
                f.write(raw_bytes)
            log_audit("SUCCESS: Keyboard RGB zones written.")
            return 0
        except Exception as e:
            log_audit(f"ERROR: Failed writing to {HP_WMI_RGB_PATH}: {str(e)}")
            return 3
    else:
        log_audit("NOTICE: hp-wmi rgb_zones node not present.")
        return 0


def main():
    if len(sys.argv) < 3:
        sys.stderr.write("Usage: nuxarchy-hardware-helper <command> <argument>\n")
        sys.stderr.write("Commands:\n")
        sys.stderr.write("  set-platform-profile <low-power|balanced|performance>\n")
        sys.stderr.write("  set-fan-mode <auto|max>\n")
        sys.stderr.write("  set-keyboard-colors <24-hex-chars>\n")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    arg = sys.argv[2]

    if cmd == "set-platform-profile":
        sys.exit(set_platform_profile(arg))
    elif cmd == "set-fan-mode":
        sys.exit(set_fan_mode(arg))
    elif cmd == "set-keyboard-colors":
        sys.exit(set_keyboard_colors(arg))
    else:
        log_audit(f"REJECTED: Unknown command '{cmd}'.")
        sys.exit(1)


if __name__ == "__main__":
    main()
