"""
Unit Tests: Telemetry Parsers
"""

import unittest
from nuxarchy.backend.capability import CapabilityDetector
from nuxarchy.backend.telemetry.cpu_monitor import CpuMonitor, CpuTelemetry
from nuxarchy.backend.telemetry.gpu_amd_monitor import AmdGpuMonitor, AmdGpuTelemetry
from nuxarchy.backend.telemetry.gpu_nvidia_monitor import NvidiaGpuMonitor, NvidiaGpuTelemetry
from nuxarchy.backend.telemetry.memory_monitor import MemoryMonitor, MemoryTelemetry
from nuxarchy.backend.telemetry.network_monitor import NetworkMonitor, NetworkTelemetry
from nuxarchy.backend.telemetry.system_monitor import SystemSampler, SystemSnapshot


class TestTelemetryParsers(unittest.TestCase):
    def test_cpu_monitor(self):
        monitor = CpuMonitor()
        data = monitor.sample()
        self.assertIsInstance(data, CpuTelemetry)
        self.assertGreaterEqual(data.total_utilization, 0.0)
        self.assertLessEqual(data.total_utilization, 100.0)
        self.assertGreater(len(data.per_core_utilization), 0)

    def test_amd_gpu_monitor(self):
        monitor = AmdGpuMonitor()
        data = monitor.sample()
        self.assertIsInstance(data, AmdGpuTelemetry)
        self.assertGreaterEqual(data.utilization_percent, 0.0)
        self.assertGreaterEqual(data.vram_total_mb, 0.0)

    def test_nvidia_gpu_monitor(self):
        monitor = NvidiaGpuMonitor()
        data = monitor.sample()
        self.assertIsInstance(data, NvidiaGpuTelemetry)
        self.assertGreaterEqual(data.utilization_gpu_percent, 0.0)
        self.assertGreaterEqual(data.vram_total_mb, 1024.0)

    def test_memory_monitor(self):
        monitor = MemoryMonitor()
        data = monitor.sample()
        self.assertIsInstance(data, MemoryTelemetry)
        self.assertGreater(data.total_ram_mb, 0.0)
        self.assertGreater(data.used_ram_mb, 0.0)
        self.assertGreaterEqual(data.ram_utilization_percent, 0.0)
        self.assertLessEqual(data.ram_utilization_percent, 100.0)

    def test_network_monitor(self):
        monitor = NetworkMonitor()
        data = monitor.sample()
        self.assertIsInstance(data, NetworkTelemetry)
        self.assertGreaterEqual(data.download_kbps, 0.0)
        self.assertGreaterEqual(data.upload_kbps, 0.0)

    def test_system_sampler(self):
        caps = CapabilityDetector(simulation_mode=True).detect()
        sampler = SystemSampler(caps)
        snap = sampler.sample()
        self.assertIsInstance(snap, SystemSnapshot)
        self.assertGreater(snap.timestamp, 0.0)
        self.assertIsNotNone(snap.cpu)
        self.assertIsNotNone(snap.memory)


if __name__ == "__main__":
    unittest.main()
