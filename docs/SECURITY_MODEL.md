# NUXARCHY: Security & Privilege Architecture

## 1. Core Security Principles

1. **Principle of Least Privilege**:
   The entire graphical user interface, rendering loop, game scanner, and telemetry engine runs strictly under the desktop user's unprivileged context (`UID >= 1000`). Under no circumstances is the GUI executed as `root`. If launched under `sudo`, the application logs a security alert and drops privileges or safely exits.

2. **Read-Only Telemetry**:
   All hardware monitoring (CPU %, frequencies, core temperatures, GPU telemetry, RAM metrics, and network throughput) relies exclusively on world-readable Linux interfaces:
   - `/proc/stat`, `/proc/meminfo`, `/proc/net/dev`
   - `/sys/class/hwmon/` (read permissions granted to standard users)
   - `/sys/class/drm/`
   - NVIDIA NVML (C library API allows querying temperatures and clocks without root)

3. **Narrowly-Scoped Privileged Helper**:
   Hardware state modifications (e.g., writing to `/sys/firmware/acpi/platform_profile` or writing verified WMI fan control nodes) are mediated exclusively through a standalone, narrowly-scoped helper script (`nuxarchy-hardware-helper`) authenticated via **Polkit** (`org.freedesktop.policykit`).

---

## 2. Privileged Action Boundary & Helper Specification

### Polkit Action Definition: `com.nuxarchy.hub.policy`
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE policyconfig PUBLIC
 "-//freedesktop//DTD PolicyKit Policy Configuration 1.0//EN"
 "http://www.freedesktop.org/standards/PolicyKit/1/policyconfig.dtd">
<policyconfig>
  <vendor>Nuxarchy Linux</vendor>
  <vendor_url>https://github.com/nuxarchy</vendor_url>
  <icon_name>nuxarchy</icon_name>
  <action id="com.nuxarchy.hub.hardware-control">
    <description>Apply hardware performance and fan settings</description>
    <message>Authentication is required to adjust hardware cooling and performance profiles</message>
    <defaults>
      <allow_any>no</allow_any>
      <allow_inactive>no</allow_inactive>
      <allow_active>auth_admin_keep</allow_active>
    </defaults>
    <annotate key="org.freedesktop.policykit.exec.path">/usr/lib/nuxarchy/nuxarchy-hardware-helper</annotate>
  </action>
</policyconfig>
```

### Strict Validation Rules in `nuxarchy-hardware-helper`
1. **Whitelisted Commands**:
   - `set-platform-profile <profile>`: Allowed values strictly restricted to: `['low-power', 'balanced', 'performance']`.
   - `set-fan-mode <mode>`: Allowed values strictly restricted to: `['auto', 'max']`.
   - `set-keyboard-colors <hex_zones>`: Must match exact regex `^[0-9a-fA-F]{24}$` (4 zones × 3 bytes RGB).
2. **Path Sanitization**:
   - The helper only interacts with predefined kernel sysfs paths (`/sys/firmware/acpi/platform_profile`, `/sys/devices/platform/hp-wmi/`).
   - No user-supplied file paths or arbitrary arguments are accepted.
3. **Execution Safety**:
   - Zero shell invocation (`shell=False` in Python / `execve` with fixed vectors).
   - Input arguments undergo length and boundary verification before any file descriptor write.
   - Any out-of-bounds parameter immediately aborts execution with a nonzero exit code and logs a structured security notice to `systemd-journald`.

---

## 3. Hardware Safety & Failsafe Protections

1. **No Silent Thermal Override**:
   The application never disables hardware thermal throttling or modifies critical ACPI thermal trip points (`critical_temp`). If a system approaches dangerous temperatures (>95°C on CPU or >87°C on GPU), the UI elevates visual warning alerts and refuses any manual fan reductions.

2. **No Unverified EC Register Tampering**:
   Blindly writing to Embedded Controller (EC) I/O ports (`/dev/port` or EC memory offsets) without model-specific reverse engineering can cause battery disconnects, thermal runaway, or firmware lockups. The application uses only verified kernel driver abstractions (`hp-wmi`, ACPI `platform_profile`).

3. **Reversible Firmware Changes**:
   Any setting changed via the UI can be restored to system defaults with a single click ("Restore Factory Defaults").
