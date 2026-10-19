# NUXARCHY: Hardware Compatibility Guide

## 1. Universal Hardware Architecture & Target Specification

NUXARCHY is engineered with automatic hardware discovery for modern Linux gaming laptops, convertibles, and high-performance workstations:

```
Platform Architecture:   Modern Linux Gaming Laptops & Mobile Workstations
Motherboard / SMBIOS:    Standard Linux DMI BaseBoard & SMBIOS Probing
Firmware / ACPI:         ACPI Platform Profiles (low-power, balanced, performance)
Processors Supported:    Multi-Core x86_64 CPUs (AMD Ryzen 5000-8000/AI Series, Intel Core)
Integrated Graphics:     AMD Radeon Graphics (amdgpu DRM), Intel Iris/Arc
Discrete Graphics:       NVIDIA GeForce RTX / GTX Dedicated GPUs (via NVML & PRIME)
Memory Management:       Automatic RAM & Swap allocation monitoring
Target Desktop:          Arch Linux, Fedora, Ubuntu/Debian (Wayland / Hyprland / KDE / GNOME)
```

---

## 2. Linux Kernel Driver & Interface Mapping

### 2.1 Platform Management & ACPI (`platform_profile` & WMI)
- **Kernel Drivers**: `platform_profile`, `hp-wmi`, `asus-wmi`, `ideapad_laptop`
- **ACPI Platform Profile Interface**:
  - Exposed via `/sys/firmware/acpi/platform_profile` and `/sys/firmware/acpi/platform_profile_choices`
  - Canonical profiles: `low-power` (Quiet/Eco), `balanced` (Default), `performance` (Performance Boost)

### 2.2 AMD Processor & Sensor Subsystem
- **Kernel Modules**: `k10temp` (or `zenpower3` dkms module), `amd_pstate` (or `amd_pstate_epp`)
- **Frequency Scaling**:
  - Driver: `amd-pstate-epp`
  - Path: `/sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq`
  - Energy Performance Preference: `/sys/devices/system/cpu/cpu*/cpufreq/energy_performance_preference` (`performance`, `balance_performance`, `balance_power`, `power`)
- **Thermal & Power Sensors**:
  - Sensor Path: `/sys/class/hwmon/hwmon*/` where name is `k10temp`
  - Inputs:
    - `temp1_input`: `Tctl` (Control Temperature, in millidegrees Celsius)
    - `temp2_input`: `Tdie` (Actual Die Temperature)

### 2.3 AMD Radeon Integrated Graphics (amdgpu)
- **Kernel Module**: `amdgpu`
- **DRM Interface**: `/sys/class/drm/card*/device/`
- **Telemetry Nodes**:
  - Utilization: `/sys/class/drm/card*/device/gpu_busy_percent`
  - Clocks: `/sys/class/drm/card*/device/pp_dpm_sclk`
  - Temperature: `/sys/class/drm/card*/device/hwmon/hwmon*/temp1_input`
  - VRAM: `/sys/class/drm/card*/device/mem_info_vram_used` & `mem_info_vram_total`

### 2.4 NVIDIA Dedicated Graphics GPUs (RTX / GTX Series)
- **Kernel Module**: `nvidia`, `nvidia_modeset`, `nvidia_uvm` (Proprietary / DKMS)
- **Primary Telemetry Interface**: **NVML (NVIDIA Management Library)** via `libnvidia-ml.so.1`
- **Available Metrics**:
  - GPU Core Utilization (%)
  - Memory Utilization (%)
  - VRAM Used & Total (Bytes)
  - Temperature (°C) & Thermal Limits
  - Core & Memory Clock Frequencies (MHz)
  - Power Consumption (Milliwatts) & Power Limits (W)
  - PCIe Link Generation and Width
  - Performance State (P-State P0 - P8)
  - Fan Speed (%) when exposed by VBIOS / mobile driver

### 2.5 Multi-Zone RGB Keyboard Subsystem
- **Detection**:
  - DMI/SMBIOS probing detects available multi-zone RGB keyboard hardware.
  - Controlled either via:
    1. ACPI WMI command interface (via platform kernel module or `/sys/devices/platform/`).
    2. Embedded USB microcontroller exposed via HID raw interfaces.
    3. Integration with **OpenRGB** daemon (`openrgb --server`) when running.
- **Fail-safe Strategy**:
  - The application probes available RGB backends in order of safety:
    1. OpenRGB SDK (if OpenRGB daemon is active, port 6742).
    2. Linux WMI / sysfs LED nodes.
    3. Custom privileged daemon socket.
  - If no backend is detected or writable, the UI disables hardware lighting controls, displays a clear informational status, and allows software preview simulation without errors.

---

## 3. Multi-Vendor & Generic Hardware Compatibility

The architecture is built around an **Adapter Pattern** so that multi-vendor hardware is seamlessly supported:

| Hardware Vendor / System | Platform Profile Backend | Thermal & Fan Backend | Lighting Backend |
| :--- | :--- | :--- | :--- |
| **Linux Gaming Laptops (HP Series)** | `hp-wmi` + `power-profiles-daemon` | `hp-wmi` + Linux hwmon | WMI 4-Zone Adapter / OpenRGB |
| **HP Victus Laptops** | `hp-wmi` platform profile | Linux hwmon | Single-zone / White backlight adapter |
| **Lenovo Legion Laptops** | `ideapad_laptop` platform profile | Linux hwmon | OpenRGB / Lenovo Legion LED adapter |
| **ASUS ROG / TUF Laptops** | `asus-wmi` platform profile | `asus-nb-wmi` hwmon | `asusctl` / OpenRGB |
| **Generic / Custom Desktop** | `power-profiles-daemon` or CPUFreq | Linux hwmon (`coretemp`, `nouveau`, `amdgpu`) | OpenRGB SDK |

### Capability Registry Matrix
At startup, the application populates a `CapabilityRegistry`:
- `CAN_MONITOR_CPU`: True (always available on Linux)
- `CAN_MONITOR_GPU`: True (if AMD/Intel/NVIDIA drivers present)
- `CAN_MONITOR_RAM`: True (always available)
- `CAN_SWITCH_PLATFORM_PROFILE`: True if `/sys/firmware/acpi/platform_profile` exists
- `CAN_CONTROL_FANS`: True only if tested writable fan controls exist
- `CAN_CONTROL_LIGHTING`: True only if an active RGB adapter is confirmed
- `CAN_SWITCH_GPU_MODE`: True if dual GPU setup is detected (offers PRIME offload and MUX instructions)
