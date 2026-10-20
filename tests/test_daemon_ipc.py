"""
NUXARCHY Automated D-Bus IPC Contract Tests
Tests the D-Bus interface methods and signatures of org.nuxarchy.Daemon.
"""

import unittest
from unittest.mock import MagicMock
from nuxarchy.services.daemon import NuxarchyInterface, DBUS_SERVICE_NAME, DBUS_OBJECT_PATH
from nuxarchy.services.daemon_client import DaemonClient


class TestDaemonIpcContract(unittest.TestCase):
    def setUp(self):
        self.interface = NuxarchyInterface()

    def test_interface_constants(self):
        self.assertEqual(DBUS_SERVICE_NAME, "org.nuxarchy.Daemon")
        self.assertEqual(DBUS_OBJECT_PATH, "/org/nuxarchy/Daemon")

    def test_get_telemetry_metrics_contract(self):
        """Verify get_telemetry_metrics returns all required a{sd} keys."""
        metrics = self.interface.get_telemetry_metrics()
        self.assertIsInstance(metrics, dict)

        required_keys = [
            "cpu_temp",
            "gpu_temp",
            "cpu_usage",
            "gpu_usage",
            "cpu_freq_mhz",
            "gpu_freq_mhz",
            "vram_used_mb",
            "vram_total_mb",
            "ram_used_mb",
            "ram_total_mb",
            "cpu_fan_rpm",
            "gpu_fan_rpm",
            "current_pwm",
            "battery_pct",
            "battery_health_pct",
            "power_draw_watts",
        ]
        for key in required_keys:
            self.assertIn(key, metrics, f"Missing telemetry metric: {key}")
            self.assertIsInstance(metrics[key], (int, float), f"Metric {key} must be float/int")

    def test_platform_profile_contract(self):
        """Verify platform profile query and setter contracts."""
        profiles = self.interface.get_available_platform_profiles()
        self.assertIsInstance(profiles, list)
        self.assertTrue(len(profiles) > 0)

        cur = self.interface.get_platform_profile()
        self.assertIsInstance(cur, str)

        ok = self.interface.set_platform_profile("balanced")
        self.assertTrue(ok)

    def test_fan_mode_and_curve_contract(self):
        """Verify fan mode and custom curve setters/getters."""
        ok_mode = self.interface.set_fan_mode("auto")
        self.assertTrue(ok_mode)
        self.assertEqual(self.interface.get_fan_mode(), "auto")

        test_curve = [(30.0, 20.0), (50.0, 40.0), (70.0, 70.0), (85.0, 100.0)]
        ok_curve = self.interface.set_custom_fan_curve(test_curve)
        self.assertTrue(ok_curve)

        ret_curve = self.interface.get_custom_fan_curve()
        self.assertEqual(len(ret_curve), 4)

    def test_gpu_switch_contract(self):
        """Verify GPU status dict has required keys."""
        st = self.interface.get_gpu_status()
        self.assertIn("current_mode", st)
        self.assertIn("pending_mode", st)
        self.assertIn("requires_reboot", st)
        self.assertIn("backend", st)

        ok = self.interface.set_gpu_mode("hybrid")
        self.assertTrue(ok)

    def test_undervolt_contract(self):
        """Verify undervolt status and parameter ranges."""
        st = self.interface.get_undervolt_status()
        self.assertIn("supported", st)
        self.assertIn("core_offset_mv", st)
        self.assertIn("cache_offset_mv", st)

        # Apply offset and limits
        ok_uv = self.interface.set_undervolt_offset(-50, -50)
        ok_pl = self.interface.set_power_limits(45, 65)
        self.assertIsInstance(ok_uv, bool)
        self.assertIsInstance(ok_pl, bool)

    def test_battery_limit_contract(self):
        """Verify battery charge limit gets and sets 80 and 100."""
        ok80 = self.interface.set_battery_limit(80)
        self.assertTrue(ok80)
        self.assertEqual(self.interface.get_battery_limit(), 80)

        ok100 = self.interface.set_battery_limit(100)
        self.assertTrue(ok100)
        self.assertEqual(self.interface.get_battery_limit(), 100)

    def test_lighting_contract(self):
        """Verify lighting mode and 4-zone colors."""
        ok = self.interface.set_lighting("static", ["#00E5FF", "#00E5FF", "#FF0552", "#FF0552"], 100, 50)
        self.assertTrue(ok)

    def test_network_boost_contract(self):
        """Verify network booster and Dual Force status."""
        ok = self.interface.set_network_boost(True, True)
        self.assertTrue(ok)
        st = self.interface.get_network_boost_status()
        self.assertTrue(st["enabled"])
        self.assertTrue(st["dual_force"])

    def test_game_optimizer_contract(self):
        """Verify optimizer summary returns freed_mb, governor, boosted_pids."""
        res = self.interface.run_game_optimizer()
        self.assertIn("freed_mb", res)
        self.assertIn("governor", res)
        self.assertIn("boosted_pids", res)

    def test_daemon_client_fallback_resilience(self):
        """Verify DaemonClient functions safely without active D-Bus."""
        client = DaemonClient.instance()
        telemetry = client.get_telemetry_metrics()
        self.assertIn("cpu_temp", telemetry)
        self.assertIn("cpu_fan_rpm", telemetry)


if __name__ == "__main__":
    unittest.main()
