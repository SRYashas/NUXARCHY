"""
NUXARCHY Fan Controller & Thermal Engine
Manages thermal discovery, PWM fan speed regulation, hysteresis, piecewise
spline/linear curve interpolation, HP EC keep-alive loop, and fail-safe thermal watchdog.

Meets HP OMEN EC specifications:
- Dynamic discovery of /sys/class/hwmon sensors matching hp, hp-wmi, omen, coretemp, k10temp, amdgpu.
- Auto (EC firmware control = 2), Max (100% manual = 255), and Custom Curve modes.
- EC Keep-Alive refresh every 1.5s to prevent Embedded Controller register resets.
- Downward hysteresis requiring 3.0 seconds elapsed and at least 3.0°C temperature drop.
- 90.0°C Watchdog and 3-strike sensor failure trip forcing emergency 100% PWM.
"""

import os
import glob
import time
import logging
import threading
from typing import List, Tuple, Dict, Optional, Callable

logger = logging.getLogger("nuxarchy.fan_controller")

DEFAULT_CURVE: List[Tuple[float, float]] = [
    (30.0, 20.0),
    (45.0, 35.0),
    (60.0, 50.0),
    (75.0, 75.0),
    (85.0, 100.0),
]

HWMON_CHIP_MATCHES = ("hp", "hp-wmi", "omen", "coretemp", "k10temp", "amdgpu")


class FanController:
    """Production-grade Fan and Thermal Controller for HP OMEN and Linux gaming laptops."""

    def __init__(
        self,
        direct_mode: bool = True,
        on_emergency_trip: Optional[Callable[[float], None]] = None,
    ):
        self.direct_mode = direct_mode
        self.on_emergency_trip = on_emergency_trip

        self._mode: str = "auto"  # "auto", "max", "custom"
        self._curve_points: List[Tuple[float, float]] = sorted(DEFAULT_CURVE, key=lambda p: p[0])

        # Sysfs path caches
        self._pwm_paths: List[str] = []
        self._pwm_enable_paths: List[str] = []
        self._fan_rpm_paths: List[str] = []
        self._temp_paths: List[str] = []

        # State tracking
        self._current_pwm: int = 0
        self._last_target_temp: float = 0.0
        self._last_high_time: float = 0.0
        self._sensor_failure_count: int = 0
        self._emergency_triggered: bool = False

        # Threading & keep-alive
        self._running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Discover hardware
        self.discover_hardware()

    def discover_hardware(self):
        """Dynamic Sysfs Discovery across /sys/class/hwmon."""
        self._pwm_paths.clear()
        self._pwm_enable_paths.clear()
        self._fan_rpm_paths.clear()
        self._temp_paths.clear()

        hwmon_base = "/sys/class/hwmon"
        if not os.path.exists(hwmon_base):
            logger.warning("Sysfs hwmon base directory %s does not exist", hwmon_base)
            return

        try:
            entries = sorted(os.listdir(hwmon_base))
        except Exception as e:
            logger.error("Failed to list %s: %s", hwmon_base, e)
            return

        for entry in entries:
            hwmon_dir = os.path.join(hwmon_base, entry)
            name_file = os.path.join(hwmon_dir, "name")
            chip_name = ""
            if os.path.exists(name_file):
                try:
                    with open(name_file, "r") as f:
                        chip_name = f.read().strip().lower()
                except Exception:
                    chip_name = ""

            # Check if chip matches target drivers
            matched = any(target in chip_name for target in HWMON_CHIP_MATCHES)
            if not matched and chip_name:
                continue

            # Collect PWM control and enable files (pwm[1-9])
            for pwm_file in glob.glob(os.path.join(hwmon_dir, "pwm[1-9]")):
                if not pwm_file.endswith("_enable"):
                    self._pwm_paths.append(pwm_file)
            for pwm_en in glob.glob(os.path.join(hwmon_dir, "pwm[1-9]_enable")):
                self._pwm_enable_paths.append(pwm_en)

            # Collect fan RPM input files (fan[1-9]_input)
            for fan_in in glob.glob(os.path.join(hwmon_dir, "fan[1-9]_input")):
                self._fan_rpm_paths.append(fan_in)

            # Collect temp input files (temp[1-9]_input)
            for temp_in in glob.glob(os.path.join(hwmon_dir, "temp[1-9]_input")):
                self._temp_paths.append(temp_in)

        logger.info(
            "Hwmon discovered: %d PWMs, %d PWM enables, %d fan RPM inputs, %d temp inputs",
            len(self._pwm_paths),
            len(self._pwm_enable_paths),
            len(self._fan_rpm_paths),
            len(self._temp_paths),
        )

    # ── Mode Control ─────────────────────────────────────────────────────────

    def get_mode(self) -> str:
        with self._lock:
            return self._mode

    def set_mode(self, mode: str) -> bool:
        """
        Switch fan cooling mode:
        - "auto": Stop keep-alive thread. Write "2" to all pwm*_enable paths (firmware EC).
        - "max": Write "1" to pwm*_enable and "255" to pwm*. Keep-alive loop active.
        - "custom": Write "1" to pwm*_enable. Run keep-alive loop with interpolation.
        """
        mode = mode.lower()
        if mode not in ("auto", "max", "custom"):
            logger.error("Invalid fan mode requested: %s", mode)
            return False

        with self._lock:
            self._mode = mode
            if mode == "auto":
                self._stop_loop()
                self._write_all_pwm_enable("2")
                self._current_pwm = 0
                logger.info("Fan mode set to AUTO (firmware EC control restored)")
                return True
            elif mode == "max":
                self._write_all_pwm_enable("1")
                self._write_all_pwm(255)
                self._current_pwm = 255
                self._ensure_loop_started()
                logger.info("Fan mode set to MAX (100% PWM Turbo lock)")
                return True
            elif mode == "custom":
                self._write_all_pwm_enable("1")
                self._ensure_loop_started()
                logger.info("Fan mode set to CUSTOM curve")
                return True

        return False

    def get_supported_modes(self) -> List[str]:
        return ["auto", "max", "custom"]

    def get_current_mode(self) -> str:
        return self.get_mode()

    def set_cooling_mode(self, mode: str):
        if mode not in ("auto", "max", "custom"):
            return False, f"Unsupported cooling mode: {mode}"
        ok = self.set_mode(mode)
        return ok, f"Mode set to {mode}"

    def get_curve(self) -> List[Tuple[float, float]]:
        with self._lock:
            return list(self._curve_points)

    def set_curve(self, points: List[Tuple[float, float]]) -> bool:
        """Validate and set custom fan curve points [(temp_c, speed_pct), ...]."""
        if not points or len(points) < 2:
            logger.error("Curve must contain at least 2 control points")
            return False

        cleaned: List[Tuple[float, float]] = []
        for temp_c, pct in points:
            temp_clamped = max(20.0, min(105.0, float(temp_c)))
            pct_clamped = max(0.0, min(100.0, float(pct)))
            cleaned.append((temp_clamped, pct_clamped))

        cleaned.sort(key=lambda p: p[0])

        with self._lock:
            self._curve_points = cleaned

        logger.info("Custom fan curve updated with %d points", len(cleaned))
        return True

    # ── Piecewise Linear Interpolation ───────────────────────────────────────

    def _interpolate_pwm(self, temp: float) -> int:
        """
        Given sorted points [(T_0, P_0), (T_1, P_1), ..., (T_n, P_n)]:
        - For T <= T_0, return int((P_0 / 100) * 255)
        - For T >= T_n, return int((P_n / 100) * 255)
        - For T_i <= T <= T_{i+1}, linear interpolation of P, converted to [0..255].
        """
        pts = self._curve_points
        if not pts:
            return 255

        if temp <= pts[0][0]:
            p = pts[0][1]
            return max(0, min(255, int(round((p / 100.0) * 255))))

        if temp >= pts[-1][0]:
            p = pts[-1][1]
            return max(0, min(255, int(round((p / 100.0) * 255))))

        for i in range(len(pts) - 1):
            t_low, p_low = pts[i]
            t_high, p_high = pts[i + 1]
            if t_low <= temp <= t_high:
                if t_high == t_low:
                    p = p_high
                else:
                    ratio = (temp - t_low) / (t_high - t_low)
                    p = p_low + ratio * (p_high - p_low)
                return max(0, min(255, int(round((p / 100.0) * 255))))

        return 255

    # ── Sensor Reading & Safety Watchdog ─────────────────────────────────────

    def get_max_temperature(self) -> float:
        """Read all discovered temp*_input files and return the maximum temperature in °C."""
        max_t = 0.0
        valid_reads = 0

        for path in self._temp_paths:
            try:
                with open(path, "r") as f:
                    val = float(f.read().strip())
                    # Millidegrees Celsius to Celsius
                    if val > 1000:
                        val = val / 1000.0
                    if 0.0 < val < 130.0:
                        valid_reads += 1
                        if val > max_t:
                            max_t = val
            except Exception:
                continue

        if valid_reads == 0 or max_t <= 0.0:
            self._sensor_failure_count += 1
        else:
            self._sensor_failure_count = 0

        return max_t

    def get_fan_rpms(self) -> Dict[str, int]:
        """Read current RPMs from all fan*_input files."""
        rpms = {}
        for idx, path in enumerate(self._fan_rpm_paths):
            try:
                with open(path, "r") as f:
                    rpms[f"fan_{idx + 1}"] = int(f.read().strip())
            except Exception:
                rpms[f"fan_{idx + 1}"] = 0
        return rpms

    def get_current_pwm(self) -> int:
        return self._current_pwm

    # ── Hysteresis & Keep-Alive Loop ─────────────────────────────────────────

    def _ensure_loop_started(self):
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._control_loop, daemon=True, name="FanKeepAlive")
            self._thread.start()

    def _stop_loop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            if threading.current_thread() != self._thread:
                self._thread.join(timeout=2.0)
        self._thread = None

    def _control_loop(self):
        """
        Runs every 1.5s:
        - Rewrites pwm*_enable = 1 and target PWM to prevent EC reset back to auto.
        - Calculates hysteresis slew.
        - Enforces 90°C thermal watchdog and 3-strike sensor failure trip.
        """
        while self._running:
            try:
                current_temp = self.get_max_temperature()
                now = time.time()

                # Watchdog Check
                if current_temp >= 90.0 or self._sensor_failure_count >= 3:
                    logger.critical(
                        "WATCHDOG EMERGENCY TRIP: temp=%.1f°C, failures=%d",
                        current_temp,
                        self._sensor_failure_count,
                    )
                    self._current_pwm = 255
                    self._write_all_pwm_enable("1")
                    self._write_all_pwm(255)
                    if not self._emergency_triggered:
                        self._emergency_triggered = True
                        if self.on_emergency_trip:
                            try:
                                self.on_emergency_trip(current_temp if current_temp > 0 else 99.0)
                            except Exception as ex:
                                logger.error("Error invoking emergency callback: %s", ex)
                    time.sleep(1.5)
                    continue
                else:
                    self._emergency_triggered = False

                with self._lock:
                    mode = self._mode

                if mode == "max":
                    self._current_pwm = 255
                    self._write_all_pwm_enable("1")
                    self._write_all_pwm(255)
                elif mode == "custom":
                    raw_target_pwm = self._interpolate_pwm(current_temp)

                    # Hysteresis Logic
                    if current_temp >= self._last_target_temp:
                        # Ramp up immediately
                        target_pwm = raw_target_pwm
                        self._last_target_temp = current_temp
                        self._last_high_time = now
                    else:
                        # Downward slew protection:
                        # Only step down if elapsed time >= 3.0s AND temp dropped >= 3.0°C
                        elapsed = now - self._last_high_time
                        temp_drop = self._last_target_temp - current_temp
                        if elapsed >= 3.0 and temp_drop >= 3.0:
                            target_pwm = raw_target_pwm
                            self._last_target_temp = current_temp
                            self._last_high_time = now
                        else:
                            # Hold previous PWM
                            target_pwm = self._current_pwm

                    self._current_pwm = target_pwm
                    self._write_all_pwm_enable("1")
                    self._write_all_pwm(target_pwm)
                elif mode == "auto":
                    break

            except Exception as e:
                logger.error("Exception in fan control loop: %s", e)

            time.sleep(1.5)

    def _write_all_pwm_enable(self, value: str):
        for path in self._pwm_enable_paths:
            try:
                with open(path, "w") as f:
                    f.write(value)
            except Exception:
                pass

    def _write_all_pwm(self, pwm_val: int):
        val_str = str(max(0, min(255, int(pwm_val))))
        for path in self._pwm_paths:
            try:
                with open(path, "w") as f:
                    f.write(val_str)
            except Exception:
                pass

    def teardown(self):
        """Teardown on service shutdown: stops worker and restores EC firmware control (2)."""
        logger.info("Tearing down FanController, restoring firmware EC control...")
        self._stop_loop()
        self._write_all_pwm_enable("2")
        logger.info("FanController teardown complete.")
