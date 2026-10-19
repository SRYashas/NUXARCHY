"""
Unit Tests: Profile Manager & Privileged Helper Security Validations
"""

import os
import tempfile
import unittest
from services.profile_manager import ProfileManager, AppSettings
from services.privileged_helper import set_platform_profile, set_fan_mode, set_keyboard_colors


class TestServicesAndSecurity(unittest.TestCase):
    def test_profile_manager_defaults_and_save(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            mgr = ProfileManager(config_dir=temp_dir)
            settings = mgr.load_settings()
            self.assertEqual(settings.polling_interval_ms, 1000)
            self.assertEqual(settings.default_performance_profile, "balanced")
            self.assertFalse(settings.start_minimized)

            # Modify and save
            settings.polling_interval_ms = 500
            settings.default_performance_profile = "performance"
            settings.start_minimized = True
            ok = mgr.save_settings(settings)
            self.assertTrue(ok)

            # Reload
            mgr2 = ProfileManager(config_dir=temp_dir)
            loaded = mgr2.load_settings()
            self.assertEqual(loaded.polling_interval_ms, 500)
            self.assertEqual(loaded.default_performance_profile, "performance")
            self.assertTrue(loaded.start_minimized)

    def test_privileged_helper_platform_profile_validation(self):
        # Valid profiles (fails with code 2 if sysfs path doesn't exist on host, but passes arg validation)
        for profile in ["low-power", "balanced", "performance"]:
            ret = set_platform_profile(profile)
            self.assertIn(ret, [0, 2], f"Expected 0 or 2 (missing sysfs) for '{profile}', got {ret}")

        # Invalid profile must return 1 (REJECTED)
        self.assertEqual(set_platform_profile("root_exploit"), 1)
        self.assertEqual(set_platform_profile("../../etc/passwd"), 1)
        self.assertEqual(set_platform_profile("; rm -rf /"), 1)

    def test_privileged_helper_fan_mode_validation(self):
        # Valid fan modes (returns 0 if executed or sysfs absent)
        self.assertEqual(set_fan_mode("auto"), 0)
        self.assertEqual(set_fan_mode("max"), 0)

        # Invalid fan mode must return 1 (REJECTED)
        self.assertEqual(set_fan_mode("turbo"), 1)
        self.assertEqual(set_fan_mode("100"), 1)
        self.assertEqual(set_fan_mode("$(reboot)"), 1)

    def test_privileged_helper_rgb_validation(self):
        # Valid 24-character hexadecimal payload (4 zones * 3 bytes RGB = 12 bytes = 24 hex characters)
        valid_hex = "00ffd1ff2a549d4edd00ffd1"
        self.assertEqual(set_keyboard_colors(valid_hex), 0)

        # Invalid lengths and characters must return 1 (REJECTED)
        self.assertEqual(set_keyboard_colors("00ffd1"), 1)  # too short
        self.assertEqual(set_keyboard_colors("00ffd1ff2a549d4edd00ffd1aa"), 1)  # too long
        self.assertEqual(set_keyboard_colors("00ffd1ff2a549d4edd00ffzz"), 1)  # invalid hex 'zz'
        self.assertEqual(set_keyboard_colors("rm -rf /sys/devices/hp;"), 1)


if __name__ == "__main__":
    unittest.main()
