"""
NUXARCHY Automated Safety Test Suite: MSR 0x150 Bitmath & Voltage Clamping
Tests:
1. Verify -50mV, -100mV, and -150mV (clamped to -120mV) produce exact 64-bit payloads for Plane 0 and Plane 2.
2. Verify positive overvoltage requests are clamped to 0mV.
"""

import unittest
from nuxarchy.backend.adapters.undervolt import pack_msr_payload, PLANE_CORE, PLANE_CACHE


class TestMsrPacking(unittest.TestCase):
    def test_plane0_minus_50mv(self):
        """Verify -50mV on Plane 0 (CPU Core) produces 0x80000011F9A00000."""
        payload = pack_msr_payload(PLANE_CORE, -50.0)
        self.assertEqual(payload, 0x80000011F9A00000)

    def test_plane2_minus_100mv(self):
        """Verify -100mV on Plane 2 (CPU Cache) produces 0x80000211F3400000."""
        payload = pack_msr_payload(PLANE_CACHE, -100.0)
        self.assertEqual(payload, 0x80000211F3400000)

    def test_hard_safety_clamp_minus_150mv(self):
        """Verify -150mV is clamped strictly to -120mV on Plane 0 (producing 0x80000011F0A00000)."""
        payload_150 = pack_msr_payload(PLANE_CORE, -150.0)
        payload_120 = pack_msr_payload(PLANE_CORE, -120.0)
        self.assertEqual(payload_150, 0x80000011F0A00000)
        self.assertEqual(payload_150, payload_120)

    def test_plane2_clamped_minus_150mv(self):
        """Verify -150mV on Plane 2 is clamped to -120mV (producing 0x80000211F0A00000)."""
        payload = pack_msr_payload(PLANE_CACHE, -150.0)
        self.assertEqual(payload, 0x80000211F0A00000)

    def test_positive_voltage_rejection(self):
        """Verify positive voltage offset requests (+25mV) are clamped to 0mV."""
        payload_pos = pack_msr_payload(PLANE_CORE, 25.0)
        payload_zero = pack_msr_payload(PLANE_CORE, 0.0)
        self.assertEqual(payload_pos, 0x8000001100000000)
        self.assertEqual(payload_pos, payload_zero)


if __name__ == "__main__":
    unittest.main()
