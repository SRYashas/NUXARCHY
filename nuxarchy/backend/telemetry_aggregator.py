"""
NUXARCHY Telemetry Aggregator Module
Asynchronous hardware sensor polling engine for CPU, GPU, VRAM, RAM, Fans, and Battery.
"""

import os
import glob
import time
import psutil
import shutil
import logging
import threading
import subprocess
from typing import Dict, Any, Optional

logger = logging.getLogger("nuxarchy.telemetry")


class TelemetryAggregator:
    """High-frequency, non-blocking telemetry aggregator for Linux gaming hardware."""

    def __init__(self):
        self._metrics: Dict[str, float] = {
            "cpu_temp": 42.0,
            "gpu_temp": 38.0,
            "cpu_usage": 5.0,
            "gpu_usage": 0.0,
            "cpu_freq_mhz": 3200.0,
            "gpu_freq_mhz": 800.0,
            "vram_used_mb": 512.0,
            "vram_total_mb": 8192.0,
            "ram_used_mb": 4096.0,
            "ram_total_mb": 16384.0,
            "cpu_fan_rpm": 2100.0,
            "gpu_fan_rpm": 1950.0,
            "current_pwm": 64.0,
            "battery_pct": 100.0,
            "battery_health_pct": 98.0,
            "power_draw_watts": 22.5,
        }
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None

        # GPU detection
        self._has_nvidia = shutil.which("nvidia-smi") is not None
        self._amd_vram_used_path: Optional[str] = None
        self._amd_vram_total_path: Optional[str] = None
        self._amd_busy_path: Optional[str] = None
        self._amd_temp_path: Optional[str] = None
        self._discover_amd_gpu()

        # Start background polling
        self.start()

    def _discover_amd_gpu(self):
        """Locate AMDGPU sysfs files."""
        for card_path in glob.glob("/sys/class/drm/card[0-9]/device"):
            vram_u = os.path.join(card_path, "mem_info_vram_used")
            vram_t = os.path.join(card_path, "mem_info_vram_total")
            busy = os.path.join(card_path, "gpu_busy_percent")
            if os.path.exists(vram_u) and os.path.exists(vram_t):
                self._amd_vram_used_path = vram_u
                self._amd_vram_total_path = vram_t
                self._amd_busy_path = busy if os.path.exists(busy) else None
                # AMD temp in hwmon
                hwmon_matches = glob.glob(os.path.join(card_path, "hwmon/hwmon*/temp1_input"))
                if hwmon_matches:
                    self._amd_temp_path = hwmon_matches[0]
                break

    def start(self):
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._poll_loop, daemon=True, name="TelemetryAggregator")
            self._thread.start()

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            if threading.current_thread() != self._thread:
                self._thread.join(timeout=1.0)
        self._thread = None

    def get_metrics(self) -> Dict[str, float]:
        with self._lock:
            return dict(self._metrics)

    def _poll_loop(self):
        while self._running:
            try:
                data = self._sample()
                with self._lock:
                    self._metrics.update(data)
            except Exception as e:
                logger.debug("Exception in telemetry sampling: %s", e)
            time.sleep(1.0)

    def _sample(self) -> Dict[str, float]:
        metrics: Dict[str, float] = {}

        # 1. CPU Usage & Frequency
        try:
            metrics["cpu_usage"] = float(psutil.cpu_percent(interval=None))
            freq = psutil.cpu_freq()
            metrics["cpu_freq_mhz"] = float(freq.current) if freq else 3200.0
        except Exception:
            pass

        # 2. System RAM (MB)
        try:
            mem = psutil.virtual_memory()
            metrics["ram_used_mb"] = float(round(mem.used / (1024 * 1024), 1))
            metrics["ram_total_mb"] = float(round(mem.total / (1024 * 1024), 1))
        except Exception:
            pass

        # 3. CPU Temperature via sensors or thermal_zone
        cpu_temp = self._read_cpu_temp()
        if cpu_temp > 0:
            metrics["cpu_temp"] = cpu_temp

        # 4. GPU Metrics (NVIDIA or AMD)
        gpu_data = self._read_gpu_metrics()
        metrics.update(gpu_data)

        # 5. Fan RPMs & PWM from sysfs hwmon
        fan_data = self._read_fans()
        metrics.update(fan_data)

        # 6. Battery Care & Power Metrics
        bat_data = self._read_battery()
        metrics.update(bat_data)

        return metrics

    def _read_cpu_temp(self) -> float:
        """Find max CPU package/core temperature."""
        max_t = 0.0
        try:
            temps = psutil.sensors_temperatures()
            for name, entries in temps.items():
                if any(k in name.lower() for k in ("coretemp", "k10temp", "cpu", "hp")):
                    for entry in entries:
                        if entry.current and entry.current > max_t:
                            max_t = float(entry.current)
        except Exception:
            pass

        if max_t > 0:
            return round(max_t, 1)

        # Fallback /sys/class/thermal
        for z in glob.glob("/sys/class/thermal/thermal_zone*/temp"):
            try:
                with open(z, "r") as f:
                    val = float(f.read().strip())
                    if val > 1000:
                        val /= 1000.0
                    if 0 < val < 120 and val > max_t:
                        max_t = val
            except Exception:
                pass

        return round(max_t, 1) if max_t > 0 else 45.0

    def _read_gpu_metrics(self) -> Dict[str, float]:
        data: Dict[str, float] = {
            "gpu_temp": 38.0,
            "gpu_usage": 0.0,
            "gpu_freq_mhz": 800.0,
            "vram_used_mb": 512.0,
            "vram_total_mb": 8192.0,
        }

        # 1. Try NVIDIA
        if self._has_nvidia:
            try:
                cmd = [
                    "nvidia-smi",
                    "--query-gpu=temperature.gpu,utilization.gpu,clocks.current.graphics,memory.used,memory.total",
                    "--format=csv,noheader,nounits",
                ]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=1.0)
                if res.returncode == 0:
                    parts = res.stdout.strip().split(",")
                    if len(parts) >= 5:
                        data["gpu_temp"] = float(parts[0].strip())
                        data["gpu_usage"] = float(parts[1].strip())
                        data["gpu_freq_mhz"] = float(parts[2].strip())
                        data["vram_used_mb"] = float(parts[3].strip())
                        data["vram_total_mb"] = float(parts[4].strip())
                        return data
            except Exception:
                pass

        # 2. Try AMDGPU sysfs
        if self._amd_vram_used_path and self._amd_vram_total_path:
            try:
                with open(self._amd_vram_used_path, "r") as f:
                    data["vram_used_mb"] = float(round(int(f.read().strip()) / (1024 * 1024), 1))
                with open(self._amd_vram_total_path, "r") as f:
                    data["vram_total_mb"] = float(round(int(f.read().strip()) / (1024 * 1024), 1))
                if self._amd_busy_path and os.path.exists(self._amd_busy_path):
                    with open(self._amd_busy_path, "r") as f:
                        data["gpu_usage"] = float(f.read().strip())
                if self._amd_temp_path and os.path.exists(self._amd_temp_path):
                    with open(self._amd_temp_path, "r") as f:
                        val = float(f.read().strip())
                        data["gpu_temp"] = round(val / 1000.0, 1) if val > 1000 else val
            except Exception:
                pass

        return data

    def _read_fans(self) -> Dict[str, float]:
        data: Dict[str, float] = {
            "cpu_fan_rpm": 2100.0,
            "gpu_fan_rpm": 1950.0,
            "current_pwm": 64.0,
        }
        rpms = []
        for fan_in in sorted(glob.glob("/sys/class/hwmon/hwmon*/fan[1-9]_input")):
            try:
                with open(fan_in, "r") as f:
                    rpms.append(float(f.read().strip()))
            except Exception:
                pass

        if len(rpms) >= 1:
            data["cpu_fan_rpm"] = rpms[0]
        if len(rpms) >= 2:
            data["gpu_fan_rpm"] = rpms[1]
        elif len(rpms) == 1:
            data["gpu_fan_rpm"] = rpms[0]

        # Read PWM
        for pwm_f in glob.glob("/sys/class/hwmon/hwmon*/pwm[1-9]"):
            if not pwm_f.endswith("_enable"):
                try:
                    with open(pwm_f, "r") as f:
                        data["current_pwm"] = float(f.read().strip())
                        break
                except Exception:
                    pass

        return data

    def _read_battery(self) -> Dict[str, float]:
        data: Dict[str, float] = {
            "battery_pct": 100.0,
            "battery_health_pct": 98.0,
            "power_draw_watts": 22.0,
        }
        bat_dirs = glob.glob("/sys/class/power_supply/BAT*")
        if not bat_dirs:
            return data

        b = bat_dirs[0]
        cap_file = os.path.join(b, "capacity")
        if os.path.exists(cap_file):
            try:
                with open(cap_file, "r") as f:
                    data["battery_pct"] = float(f.read().strip())
            except Exception:
                pass

        # Health
        for prefix in ("energy", "charge"):
            f_p = os.path.join(b, f"{prefix}_full")
            d_p = os.path.join(b, f"{prefix}_full_design")
            if os.path.exists(f_p) and os.path.exists(d_p):
                try:
                    with open(f_p, "r") as ff, open(d_p, "r") as fd:
                        full = float(ff.read().strip())
                        design = float(fd.read().strip())
                        if design > 0:
                            data["battery_health_pct"] = round((full / design) * 100.0, 1)
                            break
                except Exception:
                    pass

        # Power
        p_path = os.path.join(b, "power_now")
        if os.path.exists(p_path):
            try:
                with open(p_path, "r") as f:
                    data["power_draw_watts"] = round(float(f.read().strip()) / 1_000_000.0, 1)
            except Exception:
                pass

        return data
