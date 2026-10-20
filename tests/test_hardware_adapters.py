"""
Unit Tests: Hardware Control Adapters (Platform Profile, Fan Controller, Lighting Adapter)
"""

import os
import tempfile
import unittest
from nuxarchy.backend.adapters.platform_profile import PlatformProfileAdapter
from nuxarchy.backend.adapters.fan_controller import FanController
from nuxarchy.backend.adapters.lighting_adapter import LightingAdapter, LightingProfile, RgbColor


class TestHardwareAdapters(unittest.TestCase):
    def test_platform_profile_adapter_mappings(self):
        adapter = PlatformProfileAdapter()
        supported = adapter.get_supported_profiles()
        self.assertIn("low-power", supported)
        self.assertIn("balanced", supported)
        self.assertIn("performance", supported)

        # Test canonical mapping
        ok, msg = adapter.set_profile("quiet")
        self.assertTrue(ok)
        self.assertEqual(adapter.get_current_profile(), "low-power")

        ok, msg = adapter.set_profile("performance")
        self.assertTrue(ok)
        self.assertEqual(adapter.get_current_profile(), "performance")

        ok, msg = adapter.set_profile("extreme")
        self.assertTrue(ok)
        self.assertEqual(adapter.get_current_profile(), "performance")

        # Test invalid profile
        ok, msg = adapter.set_profile("invalid_nitro_boost")
        self.assertFalse(ok)
        self.assertIn("not supported", msg)

    def test_fan_controller(self):
        controller = FanController()
        modes = controller.get_supported_modes()
        self.assertIn("auto", modes)
        self.assertIn("max", modes)
        self.assertEqual(controller.get_current_mode(), "auto")

        # Set max mode
        ok, msg = controller.set_cooling_mode("max")
        self.assertTrue(ok)
        self.assertEqual(controller.get_current_mode(), "max")

        # Set auto mode
        ok, msg = controller.set_cooling_mode("auto")
        self.assertTrue(ok)
        self.assertEqual(controller.get_current_mode(), "auto")

        # Reject invalid mode
        ok, msg = controller.set_cooling_mode("overclock_120%")
        self.assertFalse(ok)
        self.assertIn("Unsupported", msg)

    def test_lighting_adapter_profile_persistence(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            adapter = LightingAdapter(profiles_dir=temp_dir)
            profile = LightingProfile(
                name="CyberNeon",
                mode="Wave",
                brightness=90,
                speed=65,
                direction="Right",
                zone_colors=[
                    RgbColor(0, 255, 209),
                    RgbColor(255, 42, 84),
                    RgbColor(157, 78, 221),
                    RgbColor(255, 255, 255),
                ]
            )

            # Test save
            saved = adapter.save_profile(profile)
            self.assertTrue(saved)

            # Test load
            loaded = adapter.load_profile("CyberNeon")
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded.name, "CyberNeon")
            self.assertEqual(loaded.mode, "Wave")
            self.assertEqual(loaded.brightness, 90)
            self.assertEqual(loaded.speed, 65)
            self.assertEqual(len(loaded.zone_colors), 4)
            self.assertEqual(loaded.zone_colors[0].r, 0)
            self.assertEqual(loaded.zone_colors[0].g, 255)
            self.assertEqual(loaded.zone_colors[0].b, 209)

    def test_lighting_effect_animations(self):
        adapter = LightingAdapter()
        profile = LightingProfile(mode="ColorCycle", speed=50)
        frame = adapter.calculate_animated_frame(profile, elapsed_seconds=2.0)
        self.assertEqual(len(frame), 4)

        # Test Off mode
        profile_off = LightingProfile(mode="Off")
        frame_off = adapter.calculate_animated_frame(profile_off, elapsed_seconds=0.0)
        for c in frame_off:
            self.assertEqual((c.r, c.g, c.b), (0, 0, 0))


if __name__ == "__main__":
    unittest.main()
