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

    def test_glow_card_widget(self):
        card = GlowCard(title="TEST CARD", subtitle="Testing", icon_text="⚡")
        self.assertFalse(card.is_active())
        card.set_active(True)
        self.assertTrue(card.is_active())


if __name__ == "__main__":
    unittest.main()
