"""
Unit Tests: NUXARCHY Root Hardware Daemon Lifecycle and IPC Interface
"""

import unittest
from nuxarchy.services.daemon import NuxarchyDaemon, NuxarchyInterface
from nuxarchy.services.daemon_client import DaemonClient


class TestDaemon(unittest.TestCase):
    def setUp(self):
        self.daemon = NuxarchyDaemon()
        self.client = DaemonClient.instance()

    def test_daemon_instantiation(self):
        self.assertIsInstance(self.daemon, NuxarchyInterface)
        self.assertIsNotNone(self.daemon.telemetry)
        self.assertIsNotNone(self.daemon.fan_controller)
        self.assertIsNotNone(self.daemon.undervolt)

    def test_daemon_client_telemetry_query(self):
        telemetry = self.client.get_telemetry_metrics()
        self.assertIsInstance(telemetry, dict)
        self.assertIn("cpu_temp", telemetry)
        self.assertIn("ram_used_mb", telemetry)

    def test_daemon_client_profiles(self):
        profiles = self.client.get_available_platform_profiles()
        self.assertIsInstance(profiles, list)
        self.assertTrue(len(profiles) > 0)


if __name__ == "__main__":
    unittest.main()
