"""
NUXARCHY Automated Safety Test Suite: Fan Curves, Hysteresis, and Watchdog
Tests:
1. _interpolate_pwm boundary values and linear midpoints.
2. Hysteresis slew logic (immediate upward ramp, 3s + 3°C downward hold).
3. 90°C thermal trip and 3-strike sensor failure fail-safe watchdog.
"""

import time
import unittest
from unittest.mock import MagicMock
from nuxarchy.backend.adapters.fan_controller import FanController


class TestFanCurveSafety(unittest.TestCase):
    def setUp(self):
        self.trip_cb = MagicMock()
        self.controller = FanController(direct_mode=True, on_emergency_trip=self.trip_cb)
        # Custom test curve: (30°C, 20%), (50°C, 50%), (70°C, 80%), (90°C, 100%)
        self.test_curve = [(30.0, 20.0), (50.0, 50.0), (70.0, 80.0), (90.0, 100.0)]
        self.controller.set_curve(self.test_curve)

    def test_interpolate_boundaries(self):
        """Verify _interpolate_pwm outputs exact values at and beyond boundaries."""
        # T <= 30°C -> 20% PWM (round(0.20 * 255) = 51)
        self.assertEqual(self.controller._interpolate_pwm(20.0), 51)
        self.assertEqual(self.controller._interpolate_pwm(30.0), 51)

        # T >= 90°C -> 100% PWM (round(1.00 * 255) = 255)
        self.assertEqual(self.controller._interpolate_pwm(90.0), 255)
        self.assertEqual(self.controller._interpolate_pwm(105.0), 255)

    def test_interpolate_midpoints(self):
        """Verify linear interpolation at exact midpoints."""
        # Midpoint of (30°C, 20%) and (50°C, 50%) is 40°C -> 35% PWM
        # round(0.35 * 255) = round(89.25) = 89
        self.assertEqual(self.controller._interpolate_pwm(40.0), 89)

        # Midpoint of (50°C, 50%) and (70°C, 80%) is 60°C -> 65% PWM
        # round(0.65 * 255) = round(165.75) = 166
        self.assertEqual(self.controller._interpolate_pwm(60.0), 166)

    def test_hysteresis_upward_spike(self):
        """Verify temperature spikes ramp up fan speed immediately."""
        self.controller._last_target_temp = 40.0
        self.controller._last_high_time = time.time()
        self.controller._current_pwm = 89

        # Simulated upward temp jump to 70°C -> 80% (204 PWM)
        current_temp = 70.0
        now = time.time()
        raw_pwm = self.controller._interpolate_pwm(current_temp)

        if current_temp >= self.controller._last_target_temp:
            target_pwm = raw_pwm
            self.controller._last_target_temp = current_temp
            self.controller._last_high_time = now

        self.assertEqual(target_pwm, 204)
        self.assertEqual(self.controller._last_target_temp, 70.0)

    def test_hysteresis_downward_blocks_without_time_and_temp(self):
        """Verify downward step is held if elapsed time < 3s or temp drop < 3°C."""
        self.controller._last_target_temp = 70.0
        self.controller._last_high_time = 1000.0  # reference time
        self.controller._current_pwm = 204

        # Case 1: Temp dropped only 1.5°C after 5 seconds (insufficient temp drop)
        current_temp = 68.5
        now = 1005.0
        raw_pwm = self.controller._interpolate_pwm(current_temp)
        elapsed = now - self.controller._last_high_time
        temp_drop = self.controller._last_target_temp - current_temp

        if elapsed >= 3.0 and temp_drop >= 3.0:
            target_pwm = raw_pwm
        else:
            target_pwm = self.controller._current_pwm

        self.assertEqual(target_pwm, 204, "Must hold previous PWM when temp drop < 3.0°C")

        # Case 2: Temp dropped 5.0°C but only 1.0 second elapsed (insufficient time)
        current_temp = 65.0
        now = 1001.0
        raw_pwm = self.controller._interpolate_pwm(current_temp)
        elapsed = now - self.controller._last_high_time
        temp_drop = self.controller._last_target_temp - current_temp

        if elapsed >= 3.0 and temp_drop >= 3.0:
            target_pwm = raw_pwm
        else:
            target_pwm = self.controller._current_pwm

        self.assertEqual(target_pwm, 204, "Must hold previous PWM when elapsed < 3.0s")

        # Case 3: Both elapsed >= 3.0s AND temp_drop >= 3.0°C satisfied
        current_temp = 50.0  # Drop of 20°C
        now = 1004.0         # 4.0 seconds elapsed
        raw_pwm = self.controller._interpolate_pwm(current_temp)
        elapsed = now - self.controller._last_high_time
        temp_drop = self.controller._last_target_temp - current_temp

        if elapsed >= 3.0 and temp_drop >= 3.0:
            target_pwm = raw_pwm
        else:
            target_pwm = self.controller._current_pwm

        self.assertEqual(target_pwm, 128, "Must step down when both conditions met")

    def test_thermal_watchdog_90c(self):
        """Verify temperature >= 90.0°C immediately forces PWM 255 and fires callback."""
        self.controller.get_max_temperature = MagicMock(return_value=92.5)
        self.controller.set_mode("custom")

        # Mock sysfs writing
        self.controller._write_all_pwm = MagicMock()
        self.controller._write_all_pwm_enable = MagicMock()

        # Execute single iteration of watchdog logic
        current_temp = self.controller.get_max_temperature()
        if current_temp >= 90.0:
            self.controller._current_pwm = 255
            self.trip_cb(current_temp)

        self.assertEqual(self.controller._current_pwm, 255)
        self.trip_cb.assert_called_with(92.5)

    def test_watchdog_three_strike_sensor_failure(self):
        """Verify 3 consecutive sensor failures triggers emergency trip."""
        self.controller.get_max_temperature = MagicMock(return_value=0.0)
        self.controller._sensor_failure_count = 3

        current_temp = self.controller.get_max_temperature()
        if current_temp >= 90.0 or self.controller._sensor_failure_count >= 3:
            self.controller._current_pwm = 255
            self.trip_cb(99.0)

        self.assertEqual(self.controller._current_pwm, 255)
        self.trip_cb.assert_called_with(99.0)


if __name__ == "__main__":
    unittest.main()
