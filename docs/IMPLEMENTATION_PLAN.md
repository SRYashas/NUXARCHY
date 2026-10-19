# NUXARCHY: Implementation Plan

## Overview & Execution Strategy

This implementation plan delivers a production-grade, native Linux application combining the capabilities of **HP OMEN Gaming Hub** and **HP OMEN Light Studio** on Arch Linux with NUXARCHY. Development is partitioned into distinct, testable milestones.

---

## Phase 1: Reference Analysis & Reverse-Engineering (COMPLETED)
- [x] Inspect accessible Windows reference assemblies in `AD2F1837.OMENCommandCenter...` and `AD2F1837.OMENLightStudio...`.
- [x] Extract .NET CLR metadata, exported types, constants, strings, and WMI command IDs.
- [x] Decode the HP 4-zone lighting WMI SECU packet structure and byte offsets.
- [x] Extract performance modes, thermal fan control tables, and MUX switch parameters.
- [x] Publish reference documentation (`docs/REFERENCE_ANALYSIS.md`, `docs/FEATURE_MATRIX.md`).

---

## Phase 2: Hardware Audit & Capability Architecture (COMPLETED)
- [x] Audit the Linux hardware platform architecture (x86_64 host, dynamic DMI probing, dual-GPU topology).
- [x] Map Linux kernel modules (`hp-wmi`, `amdgpu`, `nvidia`, `k10temp`).
- [x] Formulate `CapabilityRegistry` to dynamically enable/disable UI controls based on probed hardware.
- [x] Publish `docs/HARDWARE_COMPATIBILITY.md`, `docs/ARCHITECTURE.md`, and `docs/SECURITY_MODEL.md`.

---

## Phase 3: Core Framework, Backend Telemetry & Capability Engine (MILESTONE 1)
- [ ] Build the project directory structure (`app/`, `backend/`, `services/`, `tests/`, `packaging/`).
- [ ] Implement `backend/capability.py` for comprehensive read-only hardware detection.
- [ ] Implement asynchronous telemetry parsers:
  - `cpu_monitor.py` (usage, cores, frequencies, temperatures).
  - `gpu_amd_monitor.py` (Integrated GPU utilization, VRAM, temp).
  - `gpu_nvidia_monitor.py` (NVML C bindings for discrete GPU clocks, temp, power, VRAM).
  - `memory_monitor.py` (RAM used/free, swap).
  - `network_monitor.py` (RX/TX throughput).
- [ ] Implement simulated / hardware-independent fallback mode for rapid development and testing across environments.
- [ ] Implement comprehensive automated test suite (`tests/test_capability_registry.py`, `tests/test_telemetry_parsers.py`).

---

## Phase 4: Application Shell & Real-Time Dashboard (MILESTONE 2)
- [ ] Create the Qt 6 / PySide6 application foundation (`app/main.py`, `app/ui/main_window.py`).
- [ ] Implement the polished dark gaming UI design system (`app/style.qss`, `app/resources.py`):
  - Sidebar navigation (Dashboard, Performance, Thermal, GPU, Lighting, Games, Diagnostics, Settings).
  - Telemetry gauge cards, history graphs, status badges.
- [ ] Assemble `dashboard_view.py` with live streaming telemetry from the background worker thread.
- [ ] Verify non-blocking UI behavior and 60 FPS smooth rendering under Wayland.

---

## Phase 5: Hardware Management Pages (MILESTONE 3)
- [ ] **Performance Management (`performance_view.py`)**:
  - Read active ACPI platform profiles (`low-power`, `balanced`, `performance`).
  - CPU governor and Energy Performance Preference (EPP) selectors.
  - Safe profile switching via D-Bus / Polkit helper.
- [ ] **Thermal Management & Fan Control (`thermal_view.py`)**:
  - Live CPU/GPU temperature sensors and thermal throttle warning indicators.
  - Fan RPM telemetry display.
  - Fan mode selector (Auto vs. Maximum Cooling boost).
  - Clear explanations of hardware limits (no fake slider controls if firmware restricts custom curves).
- [ ] **GPU Mode Management (`gpu_view.py`)**:
  - Detection of dual GPUs (Integrated iGPU + Dedicated dGPU).
  - Identification of active rendering GPU.
  - Display power status (Active vs. Suspended / Runtime D3cold).
  - Explanation and configuration of PRIME offloading (`prime-run`).
  - Hardware MUX switch status and documentation.

---

## Phase 6: OMEN Light Studio Recreation (MILESTONE 4)
- [ ] Implement `lighting_adapter.py`:
  - 4-zone RGB packet builder conforming to the reversed WMI SECU packet layout.
  - OpenRGB integration adapter.
  - Safe mock adapter for non-RGB hardware.
- [ ] Assemble `lighting_view.py`:
  - Interactive visual 4-zone keyboard representation with clickable color pickers.
  - Static, Breathing, Color Cycle, and Wave animation generator.
  - Brightness and animation speed sliders.
  - Lighting profile save / load persistence.

---

## Phase 7: Game Discovery & Advanced Features (MILESTONE 5)
- [ ] Implement `library_scanner.py`:
  - Automatic indexing of Steam games from `steamapps/*.vdf`.
  - Detection of native Linux games and Lutris launchers.
- [ ] Assemble `games_view.py`:
  - Game grid with titles, banners, and launch buttons.
  - Per-game GPU selection (Automatic `__NV_PRIME_RENDER_OFFLOAD=1`).
  - Per-game performance profile linking.
- [ ] Assemble `diagnostics_view.py`:
  - Complete hardware audit (DMI strings, PCIe hierarchy, BIOS version, kernel modules, driver versions).
- [ ] Assemble `settings_view.py`:
  - Polling interval adjustment, autostart toggle, theme customization.

---

## Phase 8: Testing, Verification & Arch Linux Packaging (MILESTONE 6)
- [ ] Run full automated test suite on Windows / Linux testbeds.
- [x] Package the application:
  - Generate `com.nuxarchy.hub.desktop` desktop entry.
  - Generate Polkit policy `com.nuxarchy.hub.policy`.
  - Write standard `PKGBUILD` for Arch Linux `makepkg`.
  - Write detailed installation and uninstallation documentation in `README.md`.
