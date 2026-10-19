import unittest
import sys
import os
import tempfile
import shutil

from PySide6.QtWidgets import QApplication

from nuxarchy.backend.capability import CapabilityDetector
from nuxarchy.services.profile_manager import ProfileManager
from nuxarchy.ui.main_window import MainWindow
from nuxarchy.ui.splash_screen import SplashScreen
from nuxarchy.backend.telemetry.system_monitor import SystemSampler


class TestUiSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def test_main_window_lifecycle_and_all_views(self):
        detector = CapabilityDetector(simulation_mode=True)
        caps = detector.detect()

        with tempfile.TemporaryDirectory() as temp_dir:
            profile_mgr = ProfileManager(config_dir=temp_dir)
            window = MainWindow(caps, profile_mgr)
            self.assertIsNotNone(window)

            # Verify all 10 views exist (including OptimizerView)
            self.assertEqual(window.stack.count(), 10)

            # Switch through each view tab
            for idx in range(10):
                window.stack.setCurrentIndex(idx)
                self.assertEqual(window.stack.currentIndex(), idx)

            # Verify Optimizer tab selection helper
            window._select_optimizer_tab(0)
            self.assertEqual(window.stack.currentIndex(), 9)
            self.assertEqual(window.optimizer_view.stack.currentIndex(), 0)

            window._select_optimizer_tab(1)
            self.assertEqual(window.optimizer_view.stack.currentIndex(), 1)

            window._select_optimizer_tab(2)
            self.assertEqual(window.optimizer_view.stack.currentIndex(), 2)

            # Sample and update telemetry
            sampler = SystemSampler(caps)
            snap = sampler.sample()
            window._on_telemetry_updated(snap)

            window.close()

    def test_view_interactions_and_actions(self):
        detector = CapabilityDetector(simulation_mode=True)
        caps = detector.detect()

        with tempfile.TemporaryDirectory() as temp_dir:
            profile_mgr = ProfileManager(config_dir=temp_dir)
            window = MainWindow(caps, profile_mgr)

            # Test PerformanceView power mode & thermal modes
            pv = window.perf_view
            pv._select_mode("quiet")
            self.assertEqual(pv.profile_adapter.get_current_profile(), "low-power")
            pv._select_mode("performance")
            self.assertEqual(pv.profile_adapter.get_current_profile(), "performance")
            pv._set_thermal_mode("max")
            self.assertTrue(pv.btn_tc_max.isChecked())
            pv._set_thermal_mode("auto")
            self.assertTrue(pv.btn_tc_auto.isChecked())

            # Test GpuView switching
            gv = window.gpu_view
            gv._select_gpu_mode("hybrid")
            self.assertEqual(gv.current_mode, "hybrid")

            # Test Optimizer Cleaner scan
            cv = window.optimizer_view.cleaner_view
            cv._on_scan_finished(512.4)
            self.assertIn("512.4 MB", cv.lbl_space.text())

            # Test Optimizer Booster toggles
            bv = window.optimizer_view.booster_view
            bv._on_select_all(2)
            self.assertTrue(all(c.isChecked() for c in bv.check_boxes))
            bv._toggle_boost()
            self.assertEqual(bv.gauge._value, 100)
            bv._toggle_boost()
            self.assertEqual(bv.gauge._value, 0)

            # Test ProfileManager corrupted config resiliency
            corrupt_file = os.path.join(temp_dir, "config.json")
            with open(corrupt_file, "w") as f:
                f.write('{"polling_interval_ms": 500, "unknown_future_field": 9999}')
            loaded = profile_mgr.load_settings()
            self.assertEqual(loaded.polling_interval_ms, 500)

            # Test telemetry updates with zero / boundary values
            sampler = SystemSampler(caps)
            snap = sampler.sample()
            # Force boundary values to ensure no zero-division or crash
            snap.cpu.total_utilization = 0.0
            snap.cpu.temperature_celsius = 0.0
            snap.gpu_nvidia.utilization_gpu_percent = 0.0
            snap.gpu_nvidia.temperature_celsius = None
            snap.gpu_amd.utilization_percent = 0.0
            snap.gpu_amd.temperature_celsius = None
            snap.memory.used_ram_mb = 0.0
            snap.memory.total_ram_mb = 16384.0
            snap.memory.ram_utilization_percent = 0.0
            snap.network.upload_kbps = 0.0
            snap.network.download_kbps = 0.0
            snap.fan_rpm = None

            window._on_telemetry_updated(snap)
            window.close()

    def test_splash_screen_lifecycle(self):
        splash = SplashScreen()
        self.assertIsNotNone(splash)
        splash.progress.setValue(50)
        splash.lbl_status.setText("TEST PROBING...")
        self.assertEqual(splash.progress.value(), 50)
        splash.close()

    def test_live_mode_window_initialization(self):
        detector = CapabilityDetector(simulation_mode=False)
        caps = detector.detect()

        with tempfile.TemporaryDirectory() as temp_dir:
            profile_mgr = ProfileManager(config_dir=temp_dir)
            window = MainWindow(caps, profile_mgr)
            self.assertIsNotNone(window)
            self.assertIn(window.device_label_base, window.btn_device.text())
            window.close()


if __name__ == "__main__":
    unittest.main()


