import unittest
import sys
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

    def test_splash_screen_lifecycle(self):
        splash = SplashScreen()
        self.assertIsNotNone(splash)
        splash.progress.setValue(50)
        splash.lbl_status.setText("TEST PROBING...")
        self.assertEqual(splash.progress.value(), 50)
        splash.close()


if __name__ == "__main__":
    unittest.main()

