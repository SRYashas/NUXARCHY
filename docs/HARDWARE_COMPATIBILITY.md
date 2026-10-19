# NUXARCHY: Hardware Compatibility Guide

## 1. Primary Target Hardware Audit: HP OMEN 16-xd0xxx

The primary target platform for this implementation is the **HP OMEN 16 (2023/2024 AMD Edition)**:

```
Device:                  HP OMEN by HP Gaming Laptop 16-xd0xxx
Motherboard / Board ID:  HP 8BCD (Version 78.56)
BIOS:                    Insyde F.31 (HPQOEM - 2)
Processor:               AMD Ryzen 7 7840HS w/ Radeon 780M Graphics (8C/16T, Zen 4)
Integrated GPU (iGPU):   AMD Radeon 780M Graphics (amdgpu, RDNA 3, 12 CUs)
Discrete GPU (dGPU):     NVIDIA GeForce RTX 4050 Laptop GPU (6GB GDDR6, AD107M)
RAM:                     16 GB DDR5 5600 MHz Dual-Channel
Target OS / Desktop:     Arch Linux, NUXARCHY (Hyprland / Wayland compositor)
```

---

## 2. Linux Kernel Driver & Interface Mapping

### 2.1 HP Platform Management & WMI (`hp-wmi`)
- **Kernel Module**: `hp-wmi` (standard upstream driver in Linux 6.x+)
- **Device Node**: `/sys/devices/platform/hp-wmi/`
- **ACPI WMI GUID**: `5FB7F034-2C63-45e9-BE91-3D44E2C707E4`
- **WMI Methods**:
  - `0x20008` / `0x20009`: Lighting & Gaming Commands
  - `0x00052`: BIOS Configuration (MUX switch status & toggle)
- **Platform Profile Interface**:
  - Exposed via `/sys/firmware/acpi/platform_profile` and `/sys/firmware/acpi/platform_profile_choices`
  - Values supported on HP OMEN 16: `low-power` (Quiet/Eco), `balanced` (Default), `performance` (Performance Mode)
- **Hotkeys**:
  - OMEN Key (Keycode 227 / `XF86Tools` or `KEY_PROG1`) handled via `hp-wmi` input device event.

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

### 2.3 AMD Radeon 780M iGPU
- **Kernel Module**: `amdgpu`
- **DRM Interface**: `/sys/class/drm/card*/device/`
- **Telemetry Nodes**:
  - Utilization: `/sys/class/drm/card*/device/gpu_busy_percent`
  - Clocks: `/sys/class/drm/card*/device/pp_dpm_sclk`
  - Temperature: `/sys/class/drm/card*/device/hwmon/hwmon*/temp1_input`
  - VRAM: `/sys/class/drm/card*/device/mem_info_vram_used` & `mem_info_vram_total`

### 2.4 NVIDIA GeForce RTX 4050 Laptop GPU
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

### 2.5 4-Zone RGB Keyboard Subsystem
- **Detection**:
  - SMBIOS board ID `8BCD` on HP OMEN 16 models features an Insyde-controlled 4-zone RGB keyboard matrix.
  - Controlled either via:
    1. ACPI WMI command `0x20008` (via `hp-wmi` / `/sys/devices/platform/hp-wmi/` or direct WMI character device).
    2. Embedded USB microcontroller (VID:PID `03f0:...` or Sunplus/ITE keyboard MCU exposed in HID raw).
    3. Integration with **OpenRGB** daemon (`openrgb --server`) when running.
- **Fail-safe Strategy**:
  - The application probes available RGB backends in order of safety:
    1. OpenRGB SDK (if OpenRGB daemon is active, port 6742).
    2. Linux WMI / `hp-wmi` LED sysfs nodes.
    3. Custom privileged WMI helper.
  - If no backend is detected or writable, the UI disables hardware lighting controls, displays a clear informational status, and allows software preview simulation without errors.

---

## 3. Multi-Vendor & Generic Hardware Compatibility

The architecture is built around an **Adapter Pattern** so that non-HP hardware is seamlessly supported:

| Hardware Vendor / System | Platform Profile Backend | Thermal & Fan Backend | Lighting Backend |
| :--- | :--- | :--- | :--- |
| **HP OMEN Laptops (8BCD, 8A24, etc.)** | `hp-wmi` + `power-profiles-daemon` | `hp-wmi` + Linux hwmon | HP WMI 4-Zone Adapter / OpenRGB |
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
