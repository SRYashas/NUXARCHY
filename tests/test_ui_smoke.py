"""
NUXARCHY UI Smoke Tests (PyQt6)
Tests MainWindow lifecycle, 7-view navigation rail switching,
and custom widget instantiation.
"""

import sys
import unittest
from PyQt6.QtWidgets import QApplication

from nuxarchy.ui.main_window import MainWindow
from nuxarchy.ui.widgets.radial_gauge import RadialGauge
from nuxarchy.ui.widgets.fan_curve_editor import FanCurveEditor
from nuxarchy.ui.widgets.zone_keyboard import ZoneKeyboardWidget
from nuxarchy.ui.widgets.glow_card import GlowCard


class TestUiSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def test_main_window_lifecycle_and_all_7_views(self):
        window = MainWindow()
        self.assertIsNotNone(window)

        # Verify all 7 views exist in stack
        self.assertEqual(window.stack.count(), 7)

        # Switch through each view tab
        for idx in range(7):
            window._on_nav_clicked(idx)
            self.assertEqual(window.stack.currentIndex(), idx)

        # Test telemetry polling updates
        window._poll_telemetry()
        window.close()

    def test_radial_gauge_widget(self):
        gauge = RadialGauge(title="CPU TEST", unit="°C", min_val=0, max_val=100)
        gauge.set_value(65.0, subtitle="4.2 GHz")
        self.assertEqual(gauge._value, 65.0)
        self.assertEqual(gauge._subtitle, "4.2 GHz")

    def test_fan_curve_editor_widget(self):
        editor = FanCurveEditor()
        test_curve = [(30.0, 10.0), (50.0, 30.0), (70.0, 60.0), (85.0, 100.0)]
        editor.set_curve(test_curve)
        ret = editor.get_curve()
        self.assertEqual(len(ret), 4)
        editor.set_current_temperature(55.0)
        self.assertEqual(editor._current_temp, 55.0)

    def test_zone_keyboard_widget(self):
        kb = ZoneKeyboardWidget()
        kb.set_zone_color(0, "#00E5FF")
        kb.set_zone_color(1, "#00E5FF")
        kb.set_zone_color(2, "#FF0552")
        kb.set_zone_color(3, "#FF0552")
        self.assertEqual(kb._zone_colors[0], "#00E5FF")
        self.assertEqual(kb._zone_colors[3], "#FF0552")

    def test_thermal_pill_switch(self):
        from nuxarchy.ui.widgets.thermal_pill_switch import ThermalPillSwitch
        switch = ThermalPillSwitch()
        self.assertEqual(switch.current_mode(), "max")
        switch.set_mode("auto")
        self.assertEqual(switch.current_mode(), "auto")
        switch.set_mode("manual")
        self.assertEqual(switch.current_mode(), "manual")

    def test_performance_view_and_manual_fan(self):
        from nuxarchy.ui.views.performance_view import PerformanceView
        pv = PerformanceView()
        self.assertIsNotNone(pv)

        # Test power mode selection
        pv._on_power_mode_clicked("eco")
        self.assertTrue(pv.card_eco.is_active())
        self.assertFalse(pv.card_perf.is_active())

        pv._on_power_mode_clicked("performance")
        self.assertTrue(pv.card_perf.is_active())
        self.assertFalse(pv.card_eco.is_active())

        # Test thermal pill switch toggle
        pv._on_thermal_mode_changed("manual")
        self.assertEqual(pv.thermal_stack.currentIndex(), 1)
        pv._on_thermal_mode_changed("auto")
        self.assertEqual(pv.thermal_stack.currentIndex(), 0)

        # Test telemetry update
        metrics = {
            "cpu_temp_c": 89.0,
            "gpu_temp_c": 51.0,
            "cpu_usage_pct": 23.0,
            "fan1_rpm": 6200,
        }
        pv.update_telemetry(metrics)
        self.assertEqual(pv.lbl_cpu_temp_val.text(), "89°C")
        self.assertEqual(pv.lbl_gpu_temp_val.text(), "51°C")
        self.assertEqual(pv.lbl_cpu_util_val.text(), "23%")
        self.assertEqual(pv.lbl_rpm_state_a.text(), "6200 RPM")
        self.assertEqual(pv.lbl_cpu_temp_header.text(), "CPU: 89°C")
        pv.close()


if __name__ == "__main__":
    unittest.main()
