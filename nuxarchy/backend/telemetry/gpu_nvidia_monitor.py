"""
NVIDIA Dedicated GPU Monitor (GeForce RTX 4050 Laptop GPU)
Interfaces directly with NVML (NVIDIA Management Library) C API via ctypes,
with graceful fallbacks to nvidia-smi and simulated telemetry.
"""

import os
import sys
import ctypes
import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class NvidiaGpuTelemetry:
    name: str = "NVIDIA GeForce RTX 4050 Laptop GPU"
    utilization_gpu_percent: float = 0.0
    utilization_memory_percent: float = 0.0
    vram_used_mb: float = 0.0
    vram_total_mb: float = 6144.0  # 6 GB standard on RTX 4050 mobile
    temperature_celsius: Optional[float] = None
    graphics_clock_mhz: Optional[float] = None
    memory_clock_mhz: Optional[float] = None
    power_watts: Optional[float] = None
    power_limit_watts: Optional[float] = None
    pcie_generation: int = 4
    pcie_width: int = 8
    pstate: str = "P0"
    is_active: bool = True


class NvidiaGpuMonitor:
    def __init__(self, device_name: str = "NVIDIA GeForce RTX 4050 Laptop GPU"):
        self.device_name = device_name
        self._nvml_initialized = False
        self._nvml_handle = None
        self._init_nvml()

    def _init_nvml(self):
        # Look for libnvidia-ml.so.1 (Linux) or nvml.dll (Windows)
        lib_names = ["libnvidia-ml.so.1", "libnvidia-ml.so"] if sys.platform != "win32" else ["nvml.dll"]
        self._nvml = None
        for lib in lib_names:
            try:
                self._nvml = ctypes.CDLL(lib)
                break
            except Exception:
                pass

        if self._nvml:
            try:
                ret = self._nvml.nvmlInit_v2()
                if ret == 0:
                    handle = ctypes.c_void_p()
                    dev_ret = self._nvml.nvmlDeviceGetHandleByIndex_v2(0, ctypes.byref(handle))
                    if dev_ret == 0:
                        self._nvml_handle = handle
                        self._nvml_initialized = True
            except Exception:
                self._nvml_initialized = False

    def sample(self) -> NvidiaGpuTelemetry:
        t = NvidiaGpuTelemetry(name=self.device_name)

        if self._nvml_initialized and self._nvml and self._nvml_handle:
            try:
                # 1. Utilization
                class nvmlUtilization_t(ctypes.Structure):
                    _fields_ = [("gpu", ctypes.c_uint), ("memory", ctypes.c_uint)]
                util = nvmlUtilization_t()
                if self._nvml.nvmlDeviceGetUtilizationRates(self._nvml_handle, ctypes.byref(util)) == 0:
                    t.utilization_gpu_percent = float(util.gpu)
                    t.utilization_memory_percent = float(util.memory)

                # 2. Temperature
                temp = ctypes.c_uint()
                if self._nvml.nvmlDeviceGetTemperature(self._nvml_handle, 0, ctypes.byref(temp)) == 0:
                    t.temperature_celsius = float(temp.value)

                # 3. Memory Info
                class nvmlMemory_t(ctypes.Structure):
                    _fields_ = [("total", ctypes.c_ulonglong), ("free", ctypes.c_ulonglong), ("used", ctypes.c_ulonglong)]
                mem = nvmlMemory_t()
                if self._nvml.nvmlDeviceGetMemoryInfo(self._nvml_handle, ctypes.byref(mem)) == 0:
                    t.vram_used_mb = round(mem.used / (1024 * 1024), 1)
                    t.vram_total_mb = round(mem.total / (1024 * 1024), 1)

                # 4. Clock Speeds (NVML_CLOCK_GRAPHICS = 0, NVML_CLOCK_MEM = 2)
                clk = ctypes.c_uint()
                if self._nvml.nvmlDeviceGetClockInfo(self._nvml_handle, 0, ctypes.byref(clk)) == 0:
                    t.graphics_clock_mhz = float(clk.value)
                if self._nvml.nvmlDeviceGetClockInfo(self._nvml_handle, 2, ctypes.byref(clk)) == 0:
                    t.memory_clock_mhz = float(clk.value)

                # 5. Power
                power_mw = ctypes.c_uint()
                if self._nvml.nvmlDeviceGetPowerUsage(self._nvml_handle, ctypes.byref(power_mw)) == 0:
                    t.power_watts = round(power_mw.value / 1000.0, 1)

                return t
            except Exception:
                pass

        # Fallback to nvidia-smi if NVML C API was unavailable
        return self._sample_via_smi()

    def _sample_via_smi(self) -> NvidiaGpuTelemetry:
        t = NvidiaGpuTelemetry(name=self.device_name)
        try:
            cmd = [
                "nvidia-smi",
                "--query-gpu=utilization.gpu,temperature.gpu,memory.used,memory.total,clocks.current.graphics,power.draw",
                "--format=csv,noheader,nounits"
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=1.5)
            if res.returncode == 0:
                parts = [p.strip() for p in res.stdout.strip().split(",")]
                if len(parts) >= 6:
                    t.utilization_gpu_percent = float(parts[0])
                    t.temperature_celsius = float(parts[1])
                    t.vram_used_mb = float(parts[2])
                    t.vram_total_mb = float(parts[3])
                    t.graphics_clock_mhz = float(parts[4])
                    t.power_watts = float(parts[5])
                    return t
        except Exception:
            pass

        # Simulation fallback for testing/dev environments
        t.utilization_gpu_percent = 22.0
        t.temperature_celsius = 52.0
        t.vram_used_mb = 1420.0
        t.vram_total_mb = 6144.0
        t.graphics_clock_mhz = 1755.0
        t.memory_clock_mhz = 7000.0
        t.power_watts = 35.5
        return t
