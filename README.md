# NUXARCHY: Linux-Native HP OMEN Gaming Hub Replacement

<div align="center">
  <h3>Complete Architectural Rebuild • Linux Kernel 6.1+ • D-Bus System Service • PyQt6</h3>
  <p>Production-grade replacement for HP OMEN Gaming Hub engineered specifically for Linux.</p>
</div>

![Platform](https://img.shields.io/badge/Platform-Linux%20Kernel%206.1%2B-00E5FF?style=for-the-badge)
![UI](https://img.shields.io/badge/UI-PyQt6%20%7C%20QPainter-FF0552?style=for-the-badge)
![IPC](https://img.shields.io/badge/IPC-sdbus%20%7C%20System%20Bus-FFB300?style=for-the-badge)
![Security](https://img.shields.io/badge/Capabilities-CAP__SYS__RAWIO%20%7C%20Polkit-00FF85?style=for-the-badge)

---

## Architecture Overview

NUXARCHY operates using a two-tier least-privilege architecture:
1. **Unprivileged GUI Client (`nuxarchy`)**:
   - Modern cyber-industrial desktop UI built with PyQt6 and anti-aliased `QPainter` canvas widgets.
   - Left 220px vertical navigation rail, custom `RadialGauge` telemetry gauges, interactive 2D `FanCurveEditor` spline canvas, 4-zone `ZoneKeyboardWidget`, and selectable `GlowCard` controls.
   - Connects to the system bus via `sdbus` with graceful standalone fallback.
   - Binds to physical HP OMEN keys via D-Bus signal `omen_hotkey_pressed` for instantaneous window toggling.
2. **Privileged Systemd Root Service (`nuxarchy-daemon`)**:
   - Runs as root via systemd (`nuxarchy-daemon.service`) with bounded ambient capabilities (`CAP_SYS_RAWIO`, `CAP_NET_ADMIN`, `CAP_SYS_NICE`, `CAP_DAC_OVERRIDE`).
   - Exports the `org.nuxarchy.Daemon` interface at `/org/nuxarchy/Daemon` on the D-Bus System Bus.
   - Manages ACPI platform profiles, EC keep-alive loops, 90°C thermal watchdog, MSR 0x150 undervolting, MUX graphics switching, OpenRGB TCP synchronization, Battery Care thresholds, and nftables DSCP packet prioritization.

---

## Hardware Adapter Specifications

### 1. Thermal & Fan Engine (`fan_controller.py`)
- **Dynamic Sysfs Discovery**: Scans `/sys/class/hwmon/` matching `hp`, `hp-wmi`, `omen`, `coretemp`, `k10temp`, and `amdgpu`.
- **Cooling Modes**:
  - `Auto`: Restores firmware Embedded Controller regulation (writes `2` to `pwm*_enable`).
  - `Max`: 100% PWM Turbo lock (writes `1` to `pwm*_enable` and `255` to `pwm*`).
  - `Custom`: Interactive 2D curve interpolation with 1.5s keep-alive loop.
- **Hysteresis & Slew Protection**: Upward temperature spikes ramp immediately; downward step-downs require at least 3.0 seconds elapsed and at least a 3.0°C temperature drop.
- **Fail-Safe Watchdog**: Any reading $\ge 90.0^\circ\text{C}$ or 3 consecutive sensor failures immediately forces 100% fan duty and emits the D-Bus `emergency_thermal_trip` signal.
- **Teardown**: Automatically restores EC firmware mode on daemon termination.

### 2. CPU Voltage & TDP Clamping (`undervolt.py`)
- **Intel MSR 0x150 OC Mailbox**: Packs 64-bit payloads with 11-bit two's complement offset units (`round(mv * 1.024)`) across Plane 0 (Core) and Plane 2 (Cache).
- **Hard Safety Clamp**: Strictly clamps user requests between -120 mV and 0 mV. Overvolting is unconditionally rejected.
- **Security & Lock Checks**: Probes `/sys/kernel/security/lockdown` and checks MSR bit 20 for BIOS Plundervolt locks.
- **Intel RAPL Fallback**: Dynamically clamps sustained (PL1) and peak (PL2) wattage limits via `/sys/class/powercap/intel-rapl/intel-rapl:0/`.
- **AMD Ryzen Support**: Wraps `ryzenadj --set-coall` and `--stapm-limit`.

### 3. ACPI Platform Profiles (`platform_profile.py`)
- Maps UI profiles (`eco`, `balanced`, `performance`) to kernel choices from `/sys/firmware/acpi/platform_profile_choices`.
- Pairs profile changes with CPU frequency governors (`powersave` vs `performance`).

### 4. GPU / MUX Switcher (`gpu_switch.py`)
- Controls display multiplexer between **Hybrid (Optimus)**, **Discrete (dGPU Direct)**, and **Integrated (iGPU Only)**.
- Primary backend: `supergfxctl` D-Bus (`org.supergfxctl.Daemon`).
- Fallback backend: `envycontrol` CLI.
- Provides confirmation dialogs and reboot/logout guardrails.

### 5. OMEN Light Studio (`openrgb_client.py`)
- **Engine 1**: Direct HP WMI / Kernel Multicolor sysfs (`/sys/class/leds/hp::kbd_backlight/`).
- **Engine 2**: OpenRGB Raw TCP SDK Client (`127.0.0.1:6742`) via 16-byte protocol packets (`b'ORGB'`).
- **Software Animation Engine**: Real-time animation loop for Static, Breathing, Color Cycle, and Wave across 4 keyboard zones.

### 6. Battery Care Optimizer (`battery.py`)
- Sets charge ceiling thresholds (80% / 100%) via `/sys/class/power_supply/BAT*/charge_control_end_threshold`.
- Reads battery wear percentage and live wattage discharge rates.

### 7. Network Booster & Dual Force Routing (`network_qos.py`)
- **DSCP Prioritization**: Injects an `inet nuxarchy_qos` nftables output chain marking gaming UDP/TCP ports with Expedited Forwarding (EF `0x2e`).
- **Dual Force Multi-Interface Routing**: Binds DSCP EF packets to custom routing table 200 over Ethernet while routing background traffic over Wi-Fi.
- Clean rule flushing on daemon teardown.

### 8. 1-Click Game Optimizer (`game_optimizer.py`)
- Calls `os.sync()` and writes `3` to `/proc/sys/vm/drop_caches`, calculating freed RAM.
- Sets CPU scaling governors to `performance` and triggers Feral Interactive's GameMode D-Bus service.
- Scans running game processes (Steam, Proton, Wine) and elevates scheduling priority (`nice -10`).

### 9. Hardware Hotkey Listener (`hotkey_listener.py`)
- Non-blocking select loop parsing Linux 24-byte `input_event` structs from `/dev/input/event*`.
- Captures dedicated OMEN keys (`KEY_PROG1` 148, `KEY_FAVORITES` 364, WMI `0x21a9`) to toggle GUI visibility.

---

## Installation & Setup

### Requirements
- Linux Kernel 6.1+ (Arch Linux, Fedora, Ubuntu, Debian, Pop!_OS)
- Python 3.10+
- `systemd`, `dbus`, `nftables`, `polkit`

### Setup Steps
```bash
# 1. Clone repository
git clone https://github.com/SRYashas/NUXARCHY.git
cd NUXARCHY

# 2. Install Python package
pip install -e .

# 3. Install systemd service, D-Bus policy, and Polkit rule
sudo cp packaging/org.nuxarchy.Daemon.conf /etc/dbus-1/system.d/
sudo cp packaging/nuxarchy-daemon.service /etc/systemd/system/
sudo cp packaging/com.nuxarchy.hub.policy /usr/share/polkit-1/actions/

# 4. Reload systemd and start the root daemon
sudo systemctl daemon-reload
sudo systemctl enable --now nuxarchy-daemon.service

# 5. Launch the unprivileged GUI
nuxarchy
```

---

## Running Verification Tests

```bash
pytest tests/test_fan_curve_safety.py tests/test_msr_packing.py tests/test_daemon_ipc.py -v
```
