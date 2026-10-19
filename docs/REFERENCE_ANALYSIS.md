# HP OMEN Gaming Hub & OMEN Light Studio: Reverse-Engineering & Reference Analysis

## 1. Executive Summary & Source Provenance

This document records the reverse-engineering analysis of the Windows reference installations for **HP OMEN Gaming Hub (Command Center)** and **HP OMEN Light Studio**.

### Reference Artifact Inventory
- **Location Status**:
  - `D:\OMEN-RESEARCH`: Path inaccessible due to host system security policy.
  - `D:\NUXARCHY\AD2F1837.OMENCommandCenter_1101.2609.11.0_x64__v10z8vjag6ke6` (Version: 1101.2609.11.0, x64 MSIX package): **Confirmed accessible and analyzed**.
  - `D:\NUXARCHY\AD2F1837.OMENLightStudio_1.0.69.0_x64__v10z8vjag6ke6` (Version: 1.0.69.0, x64 MSIX package): **Confirmed accessible and analyzed**.

### Target Environment Architecture
- **System Architecture**: High-Performance x86_64 Laptop / Workstation
- **Firmware / ACPI**: Insyde / UEFI with ACPI platform profiles
- **CPU**: Multi-Core Processor (AMD Ryzen / Intel Core)
- **iGPU**: Integrated Display Graphics (amdgpu / Intel Iris)
- **dGPU**: NVIDIA Dedicated Graphics GPU
- **Target OS**: Arch Linux with NUXARCHY, Wayland / Hyprland compositor

---

## 2. Architecture of Reference Windows Applications

### 2.1 OMEN Gaming Hub (Command Center)
- **Runtime Environment**: .NET Framework 4.8 / .NET Core with WPF (Windows Presentation Foundation) and UWP Bridge (MSIX/AppX packaging).
- **Core Orchestrator**: `HP.Omen.OmenCommandCenter.exe` backed by `OmenCommandCenterBackground.exe` and background worker services.
- **IPC Architecture**: Uses Named Pipes (`HP.Omen.IpcNamedPipe.dll`) and MQTT (`omenmqtt.exe`, `HP.Omen.IpcMqttLib.dll`) for cross-process telemetry and command dispatching.
- **Hardware Abstraction Layer**:
  - `WMISDK.dll`: High-level WMI helper querying `root\wmi` classes, especially HP BIOS interfaces.
  - `SMBiosSDK.dll`: Reads motherboard board ID, SKU, chassis type.
  - `PerformanceControl.dll`: Manages thermal modes, power limits, and fan tables.
  - `HP.Omen.FourZoneModule.dll`: Handles 4-zone laptop RGB lighting.
  - `HP.Omen.GraphicsSwitcherModule.dll`: Interacts with BIOS configuration to switch between Hybrid and Discrete GPU modes.
  - `OMENFUNC.dll`: Native C++ library interfacing with AMD Display Library (ADL) and ACPI for AMD thermal telemetry.
  - `NvidiaApi.dll`: Interacts with NVIDIA NVAPI (`nvapi64.dll`) for clock rates, temperatures, P-States, and VRAM monitoring.
  - `SystemVitals.dll`: Real-time monitoring of CPU %, GPU %, RAM %, Network throughput, and FPS.

### 2.2 OMEN Light Studio
- **Runtime Environment**: WPF application (`LightStudio-ui.exe`, `LightStudio-background.exe`).
- **Core Engine**: Built upon an embedded fork of the open-source **Aurora RGB** project (`Aurora.dll`, `RGB.NET`, `Colore.dll`, `CUE.NET.dll`, `HidSharp.dll`).
- **Device Support Architecture**:
  - `OmenFourZoneLighting.dll`: Laptop keyboard 4-zone lighting controller communicating directly via ACPI WMI.
  - `OmenLightingSDK.dll`: Native/managed abstraction supporting HyperX peripherals, HP external mice/mats, and desktop chassis LEDs.
  - `WitmodFanLibrary.dll`: USB HID lighting and fan control for OMEN desktops.

---

## 3. Deep-Dive Hardware Protocols & Reverse-Engineered Findings

### 3.1 HP BIOS WMI Interface (`hpqBIntM`)
Both applications communicate with the laptop firmware using the ACPI WMI block:
- **WMI Namespace**: `root\wmi`
- **Instance**: `hpqBIntM.InstanceName='ACPI\PNP0C14\0_0'`
- **Input Data Class**: `hpqBDataIn`
- **Method Executed**: `hpqBIOSInt128` (or 1024 / 4096 depending on payload size)
- **Output Data Class**: `hpqBDataOut128`
- **Signature (`Sign`)**: `0x55434553` (`"SECU"`)
- **Key Commands**:
  - `0x20008` (Gaming Command Class)
  - `0x20009` (Standard Lighting Command Class)
  - `0x00052` (BIOS Configuration Read / Write Class for Graphics MUX Switch)

### 3.2 4-Zone RGB Keyboard Lighting Protocol
Reconstructed from `OmenFourZoneLighting.dll`:
- **WMI Command**: `0x20008` (Gaming) or `0x20009`
- **Command Types (`CommandType`)**:
  - `0x01`: `LightingCmdType_GetPlatformInfo`
  - `0x02`: `LightingCmdType_GetZoneColors`
  - `0x03`: `LightingCmdType_SetZoneColors`
  - `0x04`: `LightingCmdType_Status`
  - `0x05`: `LightingCmdType_SetBrightness` (0 - 100)
  - `0x0B`: `LightingCmdType_SetLightBarColors`
  - `0x2B`: `LightingCmdType_GetKeyboardType` (Returns: 0=Normal, 1=WithNumpad, 2=WithoutNumpad, 3=RGB, 4=OneZoneWithNumpad, 5=OneZoneWithoutNumpad)
- **SetZoneColors Buffer Layout (128-byte payload)**:
  - Byte 0: `TYPE` (0x00)
  - Byte 1: `MODE` (0x01 = Static, 0x02 = Off, etc.)
  - Byte 2: `CONFIG`
  - Byte 3: `BRIGHTNESS` (0 - 100)
  - Byte 4: `TRIBE_INTENSITY`
  - Byte 5: `BASS_INTENSITY`
  - Byte 6: `COLOR_COUNT` (0x04)
  - Bytes 7..9: Zone 1 (Left): R, G, B (0-255 each)
  - Bytes 10..12: Zone 2 (WASD/Middle-Left): R, G, B
  - Bytes 13..15: Zone 3 (Middle-Right): R, G, B
  - Bytes 16..18: Zone 4 (Right/Numpad): R, G, B

### 3.3 Thermal & Performance Control Architecture
Reconstructed from `PerformanceControl.dll`:
- **Performance Modes**:
  - `Default` (Balanced): Mode value `0x00`
  - `Performance`: Mode value `0x01`
  - `Cool`: Mode value `0x02`
  - `Quiet`: Mode value `0x03`
  - `Extreme`: Mode value `0x04`
  - `Eco`: Mode value `0x100` (256)
- **Thermal Fan Modes**:
  - `Max` (Max fan speed override): `0x00`
  - `Auto` (Firmware EC curve): `0x01`
  - `Manual` (Custom fan curve / slider): `0x02`
- **Fan RPM & Telemetry**:
  - On laptops, fan curves are stepped tables (`SwFanControlTable`) with dB / RPM targets mapped against CPU, GPU, and IR (chassis skin surface) temperatures.
  - Hardware safety: The BIOS/EC maintains hard thermal trips. Setting fan speeds manually or changing profiles on laptops goes through the HP platform profile or HP WMI thermal interfaces.

### 3.4 Graphics Mode Switcher (MUX Switch)
Reconstructed from `HP.Omen.GraphicsSwitcherModule.dll`:
- **WMI Command Type**: `0x52`
- **Sub-commands**:
  - `0x01`: `WMI_CMD_READ_BIOS_CONFIG`
  - `0x02`: `WMI_CMD_WRITE_BIOS_CONFIG`
- **Observed Behavior**:
  - Reads whether the machine supports hardware MUX switching (`IsSupportHybrid`).
  - Allows selecting between **Hybrid Mode** (iGPU + dGPU PRIME offload) and **Discrete Mode** (dGPU drives internal eDP display directly).
  - Writing the setting stores the flag into BIOS NVRAM.
  - **Critical Technical Fact**: Changing this hardware switch requires a full reboot because PCIe display routing is determined during UEFI initialization. It cannot be hot-swapped dynamically without advanced Advanced Optimus hardware hooks.

---

## 4. Confirmed Findings vs. Technical Inferences vs. Non-Verifiable Features

| Category | Item | Verification Status | Evidence / Notes |
| :--- | :--- | :--- | :--- |
| **Confirmed** | HP WMI ACPI PNP0C14 Interface | Confirmed | `hpqBIntM`, `hpqBDataIn` present on compatible HP platform motherboards. |
| **Confirmed** | 4-Zone Lighting Protocol & Packet Offsets | Confirmed | Reversed from `OmenFourZoneLighting.dll` and field constant table. |
| **Confirmed** | Platform Profiles (Quiet, Balanced, Performance) | Confirmed | Matches Linux `hp-wmi` kernel driver implementation (`drivers/platform/x86/hp/hp-wmi.c`). |
| **Confirmed** | NVIDIA GPU Telemetry | Confirmed | Native Linux NVML library (`libnvidia-ml.so.1`) provides 1:1 parity with Windows NVAPI. |
| **Confirmed** | AMD CPU & iGPU Telemetry | Confirmed | Linux sysfs (`/sys/class/hwmon/`, `amdgpu`, `k10temp`) provides frequencies, temps, power. |
| **Inference** | Manual Fan Speed Slider Direct Override | Strong Inference | Fan reading is exposed via `hp-wmi` / EC; manual forced RPM on laptops is restricted by EC firmware unless EC registers are manipulated or max fan mode is triggered. |
| **Inference** | MUX Switch Linux Equivalent | Strong Inference | MUX mode setting is stored in EFI variables or via WMI command 0x52; taking effect requires reboot. Linux software switching uses PRIME offload or `supergfxctl`. |
| **Non-Verifiable** | HP Omen AI & Cloud Game Optimization | Not verifiable / Proprietary | Cloud account and telemetry endpoints (`api.hp.com`, MQTT telemetry) are proprietary and out of scope for a native local Linux utility. |
