"""
Unit Tests: NUXARCHY Lighting WMI Packet Structure & Effects
"""

import unittest
from nuxarchy.backend.adapters.lighting_adapter import LightingAdapter, LightingProfile, RgbColor


class TestLightingPacket(unittest.TestCase):
    def setUp(self):
        self.adapter = LightingAdapter()

    def test_wmi_packet_structure(self):
        profile = LightingProfile(
            name="TestProfile",
            mode="Static",
            brightness=80,
            zone_colors=[
                RgbColor(255, 0, 0),     # Zone 1: Red
                RgbColor(0, 255, 0),     # Zone 2: Green
                RgbColor(0, 0, 255),     # Zone 3: Blue
                RgbColor(255, 255, 0),   # Zone 4: Yellow
            ]
        )
        packet = self.adapter.build_wmi_packet(profile)

        # Assert total length is 128 bytes
        self.assertEqual(len(packet), 128)

        # Assert header bytes
        self.assertEqual(packet[0], 0x00)  # TYPE
        self.assertEqual(packet[1], 0x01)  # MODE (1 = Static)
        self.assertEqual(packet[3], 80)    # BRIGHTNESS
        self.assertEqual(packet[6], 4)     # COLOR_COUNT

        # Assert Zone 1 (Bytes 7, 8, 9) = RGB(255, 0, 0)
        self.assertEqual(packet[7], 255)
        self.assertEqual(packet[8], 0)
        self.assertEqual(packet[9], 0)

        # Assert Zone 2 (Bytes 10, 11, 12) = RGB(0, 255, 0)
        self.assertEqual(packet[10], 0)
        self.assertEqual(packet[11], 255)
        self.assertEqual(packet[12], 0)

        # Assert Zone 3 (Bytes 13, 14, 15) = RGB(0, 0, 255)
        self.assertEqual(packet[13], 0)
        self.assertEqual(packet[14], 0)
        self.assertEqual(packet[15], 255)

        # Assert Zone 4 (Bytes 16, 17, 18) = RGB(255, 255, 0)
        self.assertEqual(packet[16], 255)
        self.assertEqual(packet[17], 255)
        self.assertEqual(packet[18], 0)

    def test_dynamic_effect_frame_calculation(self):
        profile = LightingProfile(mode="Breathing", speed=50)
        frame1 = self.adapter.calculate_animated_frame(profile, elapsed_seconds=0.0)
        frame2 = self.adapter.calculate_animated_frame(profile, elapsed_seconds=1.5)

        self.assertEqual(len(frame1), 4)
        self.assertEqual(len(frame2), 4)
        for c in frame1 + frame2:
            self.assertGreaterEqual(c.r, 0)
            self.assertLessEqual(c.r, 255)
            self.assertGreaterEqual(c.g, 0)
            self.assertLessEqual(c.g, 255)
            self.assertGreaterEqual(c.b, 0)
            self.assertLessEqual(c.b, 255)


if __name__ == "__main__":
    unittest.main()
