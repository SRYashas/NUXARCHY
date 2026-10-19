# NUXARCHY

<div align="center">
  <img src="nuxarchy/resources/nuxarchy_logo.png" alt="NUXARCHY Logo" width="220" />
  <h3>Universal Native Linux Gaming Hub & Hardware Control Center</h3>
  <p>A native, high-performance Linux gaming hub, hardware control center, and RGB studio for modern Wayland & X11 compositors (Hyprland, Sway, KDE Plasma, GNOME, XFCE).</p>
</div>

![Platform](https://img.shields.io/badge/Platform-Universal%20Linux-00FF85?style=for-the-badge)
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
- **Operating System**: Kali Linux, Debian, Ubuntu, Arch Linux, Fedora, openSUSE, and all modern Wayland/X11 desktop environments.

---

## Installation & Deployment

### Method 1: Universal One-Click Installer (All Linux Distributions)
Clone the repository and run the automated installer:
```bash
git clone https://github.com/SRYashas/NUXARCHY.git
cd NUXARCHY
chmod +x packaging/install.sh
./packaging/install.sh
```

---

### Method 2: Manual Installation by Distribution

#### Debian / Ubuntu / Kali Linux / Linux Mint / Pop!_OS
```bash
# 1. Install system prerequisites and Python packages
sudo apt update
sudo apt install -y python3 python3-pip python3-psutil polkitd power-profiles-daemon libxcb-cursor0

# 2. Install PySide6 (Qt 6 bindings)
sudo apt install -y python3-pyside6.qtcore python3-pyside6.qtwidgets python3-pyside6.qtgui python3-pyside6.qtsvg || pip3 install --break-system-packages pyside6 psutil

# 3. Clone and install
git clone https://github.com/SRYashas/NUXARCHY.git
cd NUXARCHY
chmod +x packaging/install.sh
./packaging/install.sh
```

#### Arch Linux / Manjaro / EndeavourOS
```bash
# Via Pacman & Makepkg:
sudo pacman -S --needed python python-pyside6 python-psutil polkit power-profiles-daemon
git clone https://github.com/SRYashas/NUXARCHY.git
cd NUXARCHY/packaging
makepkg -si
```

#### Fedora / RHEL
```bash
sudo dnf install -y python3 python3-pip python3-pyside6 python3-psutil polkit power-profiles-daemon
git clone https://github.com/SRYashas/NUXARCHY.git
cd NUXARCHY
chmod +x packaging/install.sh
./packaging/install.sh
```

#### openSUSE (Tumbleweed / Leap)
```bash
sudo zypper install -y python3 python3-pip python3-pyside6 python3-psutil polkit power-profiles-daemon
git clone https://github.com/SRYashas/NUXARCHY.git
cd NUXARCHY
chmod +x packaging/install.sh
./packaging/install.sh
```

---

### Core Dependencies
- Python 3.9+
- `PySide6` (`QtWidgets`, `QtCore`, `QtGui`, `QtSvg`)
- `psutil`
- `power-profiles-daemon`
- `polkit`
- *Optional*: `nvidia-utils` (for NVML RTX GPU telemetry)

---

## Launching

Launch from your desktop application launcher (Rofi, Wofi, Hyprland application menu, KDE, GNOME, XFCE) or run from your terminal:
```bash
nuxarchy
# or via full path / python module:
/usr/bin/nuxarchy
python3 -m nuxarchy
```

### Command-Line Options
```bash
python3 -m nuxarchy --help
python3 -m nuxarchy --simulated   # Run in simulated hardware mode (useful for testing on arbitrary systems)
python3 -m nuxarchy --minimized   # Start minimized to system tray
python3 -m nuxarchy --no-splash   # Skip splash screen
```

---

## Automated Test Suite

Run the full automated test suite:
```bash
python3 -m pytest
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
