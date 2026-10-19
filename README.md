# NUXARCHY

<div align="center">
  <img src="nuxarchy/resources/nuxarchy_logo.png" alt="NUXARCHY Logo" width="220" />
  <h3>Native Arch Linux Gaming Hub & Hardware Control Center</h3>
  <p>A native, high-performance Arch Linux gaming hub, hardware control center, and RGB studio for modern Wayland compositors (Hyprland, Sway, KDE, GNOME).</p>
</div>

![Platform](https://img.shields.io/badge/Platform-Arch%20Linux%20%7C%20NUXARCHY-00FF85?style=for-the-badge)
![UI](https://img.shields.io/badge/UI-Qt%206%20%7C%20PySide6-9D4EDD?style=for-the-badge)
![Security](https://img.shields.io/badge/Security-Least%20Privilege%20%7C%20Polkit-FF2A54?style=for-the-badge)

---

## Key Features

- **Cyberpunk Loading Screen**: Native black splash screen with animated cyber telemetry, initializing hardware probes and displaying the NUXARCHY logo.
- **System Dashboard**: Real-time hardware vitals (CPU utilization & per-core clock frequencies, integrated GPU, dedicated high-performance GPU, RAM allocation, Swap usage, upload/download network speed, and fan telemetry) with smooth 60 FPS rolling history charts.
- **Performance & Power Management**: Native ACPI platform profile switching (**Quiet / Low-Power**, **Balanced / Default**, and **Performance / Extreme Boost**) via Linux ACPI `platform_profile` and `power-profiles-daemon`.
- **Thermal & Fan Control**: Real-time CPU and GPU temperature curves with thermal throttle warnings, live fan RPM readings, and **Maximum Cooling Boost** (forcing fans to 100% duty cycle) with firmware failsafe protection.
- **Hybrid Graphics (NVIDIA PRIME & MUX)**: Dual GPU topology management, dynamic runtime D3cold status monitoring, one-click PRIME offloading configuration, and hardware MUX switch documentation.
- **RGB Lighting Studio (Keyboard RGB Control)**: 4-zone RGB keyboard lighting controller with dynamic effect engines (**Static**, **Breathing**, **Color Cycle**, **Wave**) and persistent JSON lighting profile management.
- **Optimizer Suite**: Dedicated system optimizer (**Quick Setup**, **Booster**, and **Cleaner**) with real-time memory boost, optimization item toggles, and junk file disk cleaner.
- **My Games & Application Booster**: Automatic library discovery for installed Steam and Linux native titles, per-game dedicated GPU routing (`__NV_PRIME_RENDER_OFFLOAD=1`), and automated performance profile linking.
- **System Diagnostics**: Detailed hardware audit including DMI strings, Motherboard BaseBoard ID, BIOS version, PCIe hierarchy, and loaded kernel modules.
- **Zero-Prompt Root Daemon Architecture**: Dedicated background daemon (`nuxarchy-daemon.service`) for instant 24/7 telemetry and privileged ACPI writes via Unix domain socket `/run/nuxarchy/nuxarchy.sock` with zero repeated password prompts.

---

## Universal Hardware Architecture

Designed with automatic hardware probing for any modern Linux gaming laptop or workstation:
- **Processor**: Modern x86_64 Multi-Core CPUs (AMD Ryzen 5000/6000/7000/8000/AI 300 series, Intel Core 11th-15th Gen).
- **Graphics Architecture**: Dual GPU topology with automatic discovery (AMD Radeon Graphics, Intel Arc/Iris, NVIDIA GeForce RTX/GTX dedicated GPUs).
- **Cooling & Sensors**: Universal Linux `hwmon` sensor drivers (`k10temp`, `zenpower`, `coretemp`, `amdgpu`, `nvidia`).
- **Power Delivery**: Linux ACPI platform profiles (`/sys/firmware/acpi/platform_profile`) and `powerprofilesctl`.
- **Operating System**: Arch Linux, Fedora, Debian/Ubuntu, and all modern Wayland/X11 desktop environments.

---

## Installation & Deployment on Arch Linux

### Method 1: One-Click Installer
```bash
git clone https://github.com/nuxarchy/nuxarchy.git
cd nuxarchy
chmod +x packaging/install.sh
./packaging/install.sh
```

### Method 2: Arch Linux PKGBUILD (`makepkg`)
```bash
cd packaging
makepkg -si
```

### Dependencies
- Python 3.9+
- `python-pyside6` (Qt 6 bindings)
- `python-psutil`
- `power-profiles-daemon`
- `polkit`
- Optional: `nvidia-utils` (for NVML RTX GPU telemetry)

---

## Launching

Launch from your desktop application launcher (Rofi, Wofi, Hyprland application menu, KDE, GNOME) or run from terminal:
```bash
nuxarchy
# or run directly as a Python module:
python -m nuxarchy
```

### Command-Line Options
```bash
python -m nuxarchy --help
python -m nuxarchy --simulated   # Run in simulated hardware mode (useful for testing on arbitrary systems)
python -m nuxarchy --minimized   # Start minimized to system tray
python -m nuxarchy --no-splash   # Skip cinematic splash screen
```

---

## Automated Test Suite

Run the full automated test suite:
```bash
python -m pytest
```

---

## Project Documentation

Detailed reverse-engineering findings and architectural blueprints are available in `docs/`:
- [REFERENCE_ANALYSIS.md](docs/REFERENCE_ANALYSIS.md): Hardware reverse engineering analysis, .NET metadata, and WMI protocols.
- [FEATURE_MATRIX.md](docs/FEATURE_MATRIX.md): Comprehensive feature inventory, driver requirements, and implementation status.
- [HARDWARE_COMPATIBILITY.md](docs/HARDWARE_COMPATIBILITY.md): Primary hardware audit and multi-vendor adapter mapping.
- [ARCHITECTURE.md](docs/ARCHITECTURE.md): Qt 6 / PySide6 design patterns and asynchronous threading model.
- [IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md): Completed milestone execution plan.
- [SECURITY_MODEL.md](docs/SECURITY_MODEL.md): Polkit policy rules and hardware failsafe boundaries.
