"""
Unit Tests: Hardware Capability Discovery Engine
"""

import unittest
from nuxarchy.backend.capability import CapabilityDetector, HardwareCapabilities


class TestCapabilityRegistry(unittest.TestCase):
    def test_simulation_detection(self):
        detector = CapabilityDetector(simulation_mode=True)
        caps = detector.detect()

        self.assertIsInstance(caps, HardwareCapabilities)
        self.assertTrue(caps.is_hp_omen)
        self.assertTrue(caps.is_laptop)
        self.assertEqual(caps.board_name, "8BCD")
        self.assertIn("Ryzen 7 7840HS", caps.cpu_model)
        self.assertTrue(caps.has_integrated_gpu)
        self.assertTrue(caps.has_discrete_gpu)
        self.assertTrue(caps.can_monitor_cpu)
        self.assertTrue(caps.can_monitor_gpu)
        self.assertTrue(caps.has_platform_profile)
        self.assertIn("performance", caps.platform_profile_choices)
        self.assertTrue(caps.has_4zone_rgb)
        self.assertEqual(caps.lighting_backend, "hp-wmi")

    def test_live_detection(self):
        detector = CapabilityDetector(simulation_mode=False)
        caps = detector.detect()

        self.assertIsInstance(caps, HardwareCapabilities)
        self.assertIsNotNone(caps.system_vendor)
        self.assertIsNotNone(caps.cpu_model)
        self.assertGreaterEqual(caps.cpu_threads, 1)


if __name__ == "__main__":
    unittest.main()
