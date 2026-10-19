"""
NUXARCHY Hardware & System Capability Discovery Engine
Discovers host hardware, kernel drivers, thermal interfaces, power profiles, and OS details.
Runs dynamically in native Linux (sysfs/procfs/DMI), Windows (CIM/WMI), and simulation modes.
"""

import os
import sys
import platform
import subprocess
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class HardwareCapabilities:
    # Operating System & Environment
    os_name: str = "Unknown"
    os_version: str = "Unknown"
    kernel_version: str = "Unknown"
    hostname: str = "Unknown"

    # System Identification
    system_vendor: str = "Unknown"
    product_name: str = "Unknown"
    board_name: str = "Unknown"
    bios_version: str = "Unknown"
    is_supported_device: bool = True
    is_hp_omen: bool = False  # Compatibility flag
    is_laptop: bool = True

    # CPU Information
    cpu_model: str = "Unknown"
    cpu_cores: int = 1
    cpu_threads: int = 1
    cpu_scaling_driver: str = "Unknown"
    can_monitor_cpu: bool = True
    can_tune_cpu_governor: bool = False

    # GPU Information
    has_integrated_gpu: bool = False
    integrated_gpu_name: str = "None"
    has_discrete_gpu: bool = False
    discrete_gpu_name: str = "None"
    nvidia_driver_version: Optional[str] = None
    can_monitor_gpu: bool = False
    has_mux_switch: bool = False

    # Thermal & Cooling
    can_monitor_temperatures: bool = False
    can_read_fan_rpm: bool = False
    can_control_fans: bool = False
    supported_cooling_modes: List[str] = field(default_factory=list)

    # Power Management
    has_platform_profile: bool = False
    platform_profile_choices: List[str] = field(default_factory=list)
    current_platform_profile: Optional[str] = None

    # Lighting Control
    has_4zone_rgb: bool = False
    has_per_key_rgb: bool = False
    lighting_backend: str = "none"  # 'hp-wmi', 'openrgb', 'mock', 'none'

    # Privileges
    is_root: bool = False
    has_polkit: bool = False


class CapabilityDetector:
    """Probes the host environment to build the HardwareCapabilities profile."""

    def __init__(self, simulation_mode: bool = False):
        self.simulation_mode = simulation_mode

    def detect(self) -> HardwareCapabilities:
        caps = HardwareCapabilities()
        caps.is_root = (os.geteuid() == 0) if hasattr(os, "geteuid") else False

        if self.simulation_mode:
            self._apply_simulation(caps)
            return caps

        if platform.system() == "Linux":
            self._detect_linux(caps)
        elif platform.system() == "Windows":
            self._detect_windows(caps)
        else:
            self._apply_simulation(caps)

        return caps

    def _read_sysfs(self, path: str, default: str = "") -> str:
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read().strip()
        except Exception:
            pass
        return default

    def _detect_os(self, caps: HardwareCapabilities):
        caps.hostname = platform.node() or "localhost"
        sys_name = platform.system()
        if sys_name == "Linux":
            caps.kernel_version = platform.release()
            caps.os_name = "Linux"
            if os.path.exists("/etc/os-release"):
                try:
                    with open("/etc/os-release", "r", encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith("PRETTY_NAME="):
                                caps.os_name = line.split("=", 1)[1].strip('"\'')
                                break
                            elif line.startswith("NAME=") and caps.os_name == "Linux":
                                caps.os_name = line.split("=", 1)[1].strip('"\'')
                except Exception:
                    pass
            caps.os_version = caps.kernel_version
        elif sys_name == "Windows":
            caps.kernel_version = platform.version()
            rel = platform.release()
            caps.os_name = f"Windows {rel}"
            caps.os_version = platform.version()
        else:
            caps.os_name = f"{sys_name} {platform.release()}"
            caps.kernel_version = platform.version()
            caps.os_version = platform.release()

    def _detect_linux(self, caps: HardwareCapabilities):
        self._detect_os(caps)

        # 1. DMI & System identification
        caps.system_vendor = self._read_sysfs("/sys/class/dmi/id/sys_vendor", "Generic")
        caps.product_name = self._read_sysfs("/sys/class/dmi/id/product_name", "PC")
        caps.board_name = self._read_sysfs("/sys/class/dmi/id/board_name", "")
        caps.bios_version = self._read_sysfs("/sys/class/dmi/id/bios_version", "")

        chassis_type = self._read_sysfs("/sys/class/dmi/id/chassis_type", "9")
        # Chassis types 8, 9, 10, 11, 14, 30, 31, 32 represent laptops / portables
        caps.is_laptop = chassis_type in ["8", "9", "10", "11", "14", "30", "31", "32"]

        is_hp = "hp" in caps.system_vendor.lower() or "hewlett-packard" in caps.system_vendor.lower()
        caps.is_supported_device = True
        caps.is_hp_omen = is_hp

        # 2. CPU Detection
        caps.cpu_threads = os.cpu_count() or 1
        try:
            with open("/proc/cpuinfo", "r") as f:
                cores_set = set()
                for line in f:
                    if line.startswith("model name") and caps.cpu_model == "Unknown":
                        caps.cpu_model = line.split(":", 1)[1].strip()
                    elif line.startswith("core id"):
                        cores_set.add(line.split(":", 1)[1].strip())
                if cores_set:
                    caps.cpu_cores = len(cores_set)
                else:
                    caps.cpu_cores = max(1, caps.cpu_threads // 2)
        except Exception:
            caps.cpu_model = platform.processor() or "x86_64 Processor"
            caps.cpu_cores = max(1, caps.cpu_threads // 2)

        # Check cpufreq driver
        scaling_driver = self._read_sysfs("/sys/devices/system/cpu/cpu0/cpufreq/scaling_driver")
        caps.cpu_scaling_driver = scaling_driver or "generic"
        caps.can_tune_cpu_governor = os.path.exists("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor")

        # 3. GPU Detection
        self._detect_linux_gpus(caps)

        # 4. Thermal & Platform Profile Detection
        if os.path.exists("/sys/firmware/acpi/platform_profile"):
            caps.has_platform_profile = True
            caps.current_platform_profile = self._read_sysfs("/sys/firmware/acpi/platform_profile")
            choices = self._read_sysfs("/sys/firmware/acpi/platform_profile_choices")
            if choices:
                caps.platform_profile_choices = choices.split()
            else:
                caps.platform_profile_choices = ["low-power", "balanced", "performance"]

        # Check sensors
        hwmon_root = "/sys/class/hwmon"
        if os.path.exists(hwmon_root):
            try:
                hwmons = os.listdir(hwmon_root)
                caps.can_monitor_temperatures = len(hwmons) > 0
                for h in hwmons:
                    h_path = os.path.join(hwmon_root, h)
                    for entry in os.listdir(h_path):
                        if entry.startswith("fan") and entry.endswith("_input"):
                            caps.can_read_fan_rpm = True
                            break
            except Exception:
                pass

        # Platform driver cooling modes
        hp_wmi_exists = os.path.exists("/sys/devices/platform/hp-wmi")
        if is_hp or hp_wmi_exists:
            caps.supported_cooling_modes = ["auto", "max"]
            caps.can_control_fans = True
            caps.has_4zone_rgb = True
            caps.lighting_backend = "hp-wmi"
        else:
            caps.supported_cooling_modes = ["auto", "performance"]
            caps.can_control_fans = caps.has_platform_profile
            caps.lighting_backend = "none"

        # Check for OpenRGB
        if os.path.exists("/run/openrgb") or os.path.exists("/tmp/openrgb"):
            caps.lighting_backend = "openrgb"

    def _detect_linux_gpus(self, caps: HardwareCapabilities):
        # DRM inspection
        drm_path = "/sys/class/drm"
        if os.path.exists(drm_path):
            for entry in os.listdir(drm_path):
                if entry.startswith("card") and "-" not in entry:
                    vendor_path = f"/sys/class/drm/{entry}/device/vendor"
                    vendor_id = self._read_sysfs(vendor_path).lower()
                    if vendor_id == "0x1002":  # AMD
                        caps.has_integrated_gpu = True
                        caps.integrated_gpu_name = "AMD Radeon Graphics (amdgpu)"
                        caps.can_monitor_gpu = True
                    elif vendor_id == "0x8086":  # Intel
                        caps.has_integrated_gpu = True
                        caps.integrated_gpu_name = "Intel Graphics (i915/xe)"
                        caps.can_monitor_gpu = True
                    elif vendor_id == "0x10de":  # NVIDIA
                        caps.has_discrete_gpu = True
                        caps.discrete_gpu_name = "NVIDIA GeForce Dedicated GPU"
                        caps.can_monitor_gpu = True
                    elif vendor_id:
                        if not caps.has_integrated_gpu and not caps.has_discrete_gpu:
                            caps.has_integrated_gpu = True
                            caps.integrated_gpu_name = "Universal Linux Graphics"
                            caps.can_monitor_gpu = True

        # NVIDIA driver check
        if os.path.exists("/proc/driver/nvidia/version"):
            caps.has_discrete_gpu = True
            ver_text = self._read_sysfs("/proc/driver/nvidia/version")
            for part in ver_text.split():
                if part.count(".") >= 2:
                    caps.nvidia_driver_version = part
                    break
            caps.discrete_gpu_name = caps.discrete_gpu_name or "NVIDIA GeForce GPU"
            caps.can_monitor_gpu = True

        if caps.has_integrated_gpu and caps.has_discrete_gpu:
            caps.has_mux_switch = True

    def _detect_windows(self, caps: HardwareCapabilities):
        """Native Windows dynamic discovery via PowerShell CIM queries."""
        self._detect_os(caps)

        # Dynamic query via PowerShell CIM
        try:
            ps_script = (
                "$cs = Get-CimInstance Win32_ComputerSystem; "
                "$bb = Get-CimInstance Win32_BaseBoard; "
                "$bios = Get-CimInstance Win32_BIOS; "
                "$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1; "
                "$gpus = Get-CimInstance Win32_VideoController; "
                "[PSCustomObject]@{"
                "Manufacturer = $cs.Manufacturer; "
                "Model = $cs.Model; "
                "PCSystemType = $cs.PCSystemType; "
                "Board = $bb.Product; "
                "Bios = $bios.SMBIOSBIOSVersion; "
                "Cpu = $cpu.Name; "
                "Cores = $cpu.NumberOfCores; "
                "Threads = $cpu.NumberOfLogicalProcessors; "
                "Gpus = @($gpus | ForEach-Object { $_.Name })"
                "} | ConvertTo-Json"
            )
            proc = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=4
            )
            if proc.returncode == 0 and proc.stdout.strip():
                import json
                data = json.loads(proc.stdout)
                caps.system_vendor = (data.get("Manufacturer") or "Generic").strip()
                caps.product_name = (data.get("Model") or "PC").strip()
                caps.board_name = (data.get("Board") or "").strip()
                caps.bios_version = (data.get("Bios") or "").strip()

                # PCSystemType 2 is Mobile / Laptop
                sys_type = data.get("PCSystemType", 2)
                caps.is_laptop = (sys_type == 2)

                caps.cpu_model = (data.get("Cpu") or platform.processor()).strip()
                caps.cpu_cores = int(data.get("Cores") or os.cpu_count() or 1)
                caps.cpu_threads = int(data.get("Threads") or os.cpu_count() or 1)

                gpus = data.get("Gpus") or []
                if isinstance(gpus, str):
                    gpus = [gpus]
                for gpu in gpus:
                    gpu_lower = gpu.lower()
                    if "nvidia" in gpu_lower or "geforce" in gpu_lower:
                        caps.has_discrete_gpu = True
                        caps.discrete_gpu_name = gpu
                        caps.can_monitor_gpu = True
                    elif "radeon" in gpu_lower or "amd" in gpu_lower or "intel" in gpu_lower:
                        caps.has_integrated_gpu = True
                        caps.integrated_gpu_name = gpu
        except Exception:
            caps.system_vendor = "Generic"
            caps.product_name = platform.node() or "PC"
            caps.cpu_model = platform.processor() or "Multi-Core CPU"
            caps.cpu_threads = os.cpu_count() or 1
            caps.cpu_cores = max(1, caps.cpu_threads // 2)

        is_hp = "hp" in caps.system_vendor.lower() or "hewlett-packard" in caps.system_vendor.lower()
        caps.is_supported_device = True
        caps.is_hp_omen = is_hp
        caps.can_monitor_cpu = True
        caps.has_platform_profile = True
        caps.platform_profile_choices = ["low-power", "balanced", "performance"]
        caps.current_platform_profile = "balanced"
        caps.can_monitor_temperatures = True
        caps.can_read_fan_rpm = True
        caps.can_control_fans = True
        caps.supported_cooling_modes = ["auto", "max"]
        caps.has_4zone_rgb = True
        caps.lighting_backend = "hp-wmi" if is_hp else "generic"
        caps.has_mux_switch = caps.has_integrated_gpu and caps.has_discrete_gpu

    def _apply_simulation(self, caps: HardwareCapabilities):
        """Generic simulation profile providing full capability set for automated test suites."""
        caps.os_name = "Linux (Universal Workstation)"
        caps.os_version = "6.12.0-generic"
        caps.kernel_version = "6.12.0-generic"
        caps.hostname = "nuxarchy-workstation"

        caps.system_vendor = "Generic OEM"
        caps.product_name = "High-Performance Workstation Laptop"
        caps.board_name = "BaseBoard"
        caps.bios_version = "1.0.0-PROD"
        caps.is_supported_device = True
        caps.is_hp_omen = False
        caps.is_laptop = True

        caps.cpu_model = "Multi-Core x86_64 Processor"
        caps.cpu_cores = 8
        caps.cpu_threads = 16
        caps.cpu_scaling_driver = "generic-cpufreq"
        caps.can_monitor_cpu = True
        caps.can_tune_cpu_governor = True

        caps.has_integrated_gpu = True
        caps.integrated_gpu_name = "Integrated Display Graphics"
        caps.has_discrete_gpu = True
        caps.discrete_gpu_name = "Discrete Dedicated Graphics GPU"
        caps.nvidia_driver_version = "560.35.03"
        caps.can_monitor_gpu = True
        caps.has_mux_switch = True

        caps.can_monitor_temperatures = True
        caps.can_read_fan_rpm = True
        caps.can_control_fans = True
        caps.supported_cooling_modes = ["auto", "max"]

        caps.has_platform_profile = True
        caps.platform_profile_choices = ["low-power", "balanced", "performance"]
        caps.current_platform_profile = "balanced"

        caps.has_4zone_rgb = True
        caps.lighting_backend = "generic"

