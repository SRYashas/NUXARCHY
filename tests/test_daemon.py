"""
Unit Tests: NUXARCHY Root Hardware Daemon and DaemonClient
Validates socket request-response protocol, live telemetry streaming,
and privileged hardware state modification without repeated password prompts.
"""

import os
import sys
import time
import socket
import tempfile
import unittest
import threading

from nuxarchy.services.daemon import NuxarchyDaemon
from nuxarchy.services.daemon_client import DaemonClient
from nuxarchy.backend.capability import HardwareCapabilities
from nuxarchy.backend.telemetry.system_monitor import SystemSnapshot


class TestDaemon(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create temporary socket directory
        cls.temp_dir = tempfile.mkdtemp()
        cls.port = 19856
        if hasattr(socket, "AF_UNIX"):
            cls.sock_path = os.path.join(cls.temp_dir, "test_nuxarchy.sock")
        else:
            cls.sock_path = f"127.0.0.1:{cls.port}"

        cls.daemon = NuxarchyDaemon(socket_path=cls.sock_path, port=cls.port)
        cls.daemon_thread = threading.Thread(target=cls.daemon.start, daemon=True)
        cls.daemon_thread.start()
        time.sleep(0.5)

        cls.client = DaemonClient(socket_path=cls.sock_path, tcp_port=cls.port)

    @classmethod
    def tearDownClass(cls):
        cls.daemon.stop()
        time.sleep(0.3)
        os.environ.pop("NUXARCHY_DAEMON", None)
        if os.path.exists(cls.temp_dir):
            try:
                import shutil
                shutil.rmtree(cls.temp_dir, ignore_errors=True)
            except Exception:
                pass

    def test_daemon_ping(self):
        self.assertTrue(self.client.is_connected())

    def test_daemon_get_capabilities(self):
        caps = self.client.get_capabilities()
        self.assertIsInstance(caps, HardwareCapabilities)
        self.assertIsNotNone(caps.system_vendor)
        self.assertIsNotNone(caps.cpu_model)

    def test_daemon_get_snapshot(self):
        snap = self.client.get_snapshot()
        self.assertIsInstance(snap, SystemSnapshot)
        self.assertIsNotNone(snap.cpu)
        self.assertIsNotNone(snap.memory)
        self.assertGreater(snap.memory.total_ram_mb, 0)

    def test_daemon_set_platform_profile(self):
        success, msg = self.client.set_platform_profile("performance")
        self.assertTrue(success)
        self.assertIn("performance", msg.lower())

    def test_daemon_set_fan_mode(self):
        success, msg = self.client.set_fan_mode("max")
        self.assertTrue(success)
        self.assertIn("max", msg.lower())

    def test_daemon_set_rgb_zones(self):
        hex_data = "ff000000ff000000ffff00ff"  # 24 chars
        success, msg = self.client.set_rgb_zones(hex_data)
        self.assertTrue(success)

    def test_disconnected_client_resilience(self):
        bad_client = DaemonClient(socket_path="/nonexistent/path/nuxarchy.sock", tcp_port=59999)
        # Ensure methods fail gracefully without crashing
        self.assertFalse(bad_client.is_connected())
        self.assertIsNone(bad_client.get_capabilities())
        self.assertIsNone(bad_client.get_snapshot())
        success, msg = bad_client.set_platform_profile("balanced")
        self.assertFalse(success)


if __name__ == "__main__":
    unittest.main()
