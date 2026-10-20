"""
NUXARCHY Privileged Root Systemd D-Bus Service
Exports org.nuxarchy.Daemon at /org/nuxarchy/Daemon on the System Bus (sdbus).

Requires root privileges (os.geteuid() == 0).
Integrates:
- TelemetryAggregator
- FanController
- UndervoltAdapter
- PlatformProfileAdapter
- GpuSwitchAdapter
- LightingAdapter
- BatteryAdapter
- NetworkQoSAdapter
- GameOptimizerAdapter
- HotkeyListener
"""

import os
import sys
import time
import signal
import logging
from typing import Dict, List, Tuple, Any

# Graceful sdbus import with mock shim for non-Linux / test environments
try:
    import sdbus
    HAS_SDBUS = True
except ImportError:
    HAS_SDBUS = False

    class _MockDbus:
        class DbusInterfaceCommon:
            def __init_subclass__(cls, **kwargs):
                pass
            def __init__(self, *args, **kwargs):
                pass
            def export_to_dbus(self, path: str):
                pass
            def connect_to_dbus(self, name: str, path: str):
                pass

        @staticmethod
        def dbus_method(input_signature: str = "", result_signature: str = ""):
            def decorator(fn):
                fn._dbus_in = input_signature
                fn._dbus_out = result_signature
                return fn
            return decorator

        @staticmethod
        def dbus_signal(signature: str = ""):
            class _Signal:
                def __init__(self, sig):
                    self.sig = sig
                def emit(self, *args):
                    pass
            return _Signal(signature)

        @staticmethod
        def sd_bus_open_system():
            return None

        @staticmethod
        def set_default_bus(bus):
            pass

        @staticmethod
        def request_name(name: str):
            pass

    sdbus = _MockDbus()

from nuxarchy.backend.telemetry import TelemetryAggregator
from nuxarchy.backend.adapters.fan_controller import FanController
from nuxarchy.backend.adapters.undervolt import UndervoltAdapter
from nuxarchy.backend.adapters.platform_profile import PlatformProfileAdapter
from nuxarchy.backend.adapters.gpu_switch import GpuSwitchAdapter
from nuxarchy.backend.adapters.openrgb_client import LightingAdapter
from nuxarchy.backend.adapters.battery import BatteryAdapter
from nuxarchy.backend.adapters.network_qos import NetworkQoSAdapter
from nuxarchy.backend.adapters.game_optimizer import GameOptimizerAdapter
from nuxarchy.backend.adapters.hotkey_listener import HotkeyListener

logger = logging.getLogger("nuxarchy.daemon")

DBUS_SERVICE_NAME = "org.nuxarchy.Daemon"
DBUS_OBJECT_PATH = "/org/nuxarchy/Daemon"


class NuxarchyInterface(
    sdbus.DbusInterfaceCommon,
    interface_name=DBUS_SERVICE_NAME,
):
    """System Bus D-Bus Interface for NUXARCHY Hardware Daemon."""

    # D-Bus Signals
    omen_hotkey_pressed = sdbus.dbus_signal()
    emergency_thermal_trip = sdbus.dbus_signal(signature="d")

    def __init__(self):
        super().__init__()
        self.telemetry = TelemetryAggregator()
        self.platform_profile = PlatformProfileAdapter(direct_mode=True)
        self.fan_controller = FanController(
            direct_mode=True,
            on_emergency_trip=self._on_emergency_thermal_trip,
        )
        self.undervolt = UndervoltAdapter(direct_mode=True)
        self.gpu_switch = GpuSwitchAdapter(direct_mode=True)
        self.lighting = LightingAdapter(direct_mode=True)
        self.battery = BatteryAdapter(direct_mode=True)
        self.network_qos = NetworkQoSAdapter(direct_mode=True)
        self.game_optimizer = GameOptimizerAdapter(direct_mode=True)
        self.hotkey_listener = HotkeyListener(on_hotkey=self._on_hotkey)

    def _on_emergency_thermal_trip(self, temp: float):
        logger.critical("EMERGENCY THERMAL TRIP! Emitting D-Bus signal at %.1f°C", temp)
        try:
            self.emergency_thermal_trip.emit(float(temp))
        except Exception as e:
            logger.error("Failed to emit emergency signal: %s", e)

    def _on_hotkey(self):
        logger.info("OMEN Key pressed! Emitting D-Bus signal omen_hotkey_pressed")
        try:
            self.omen_hotkey_pressed.emit()
        except Exception as e:
            logger.error("Failed to emit hotkey signal: %s", e)

    # ── D-Bus Methods ────────────────────────────────────────────────────────

    @sdbus.dbus_method(result_signature="a{sd}")
    def get_telemetry_metrics(self) -> Dict[str, float]:
        metrics = self.telemetry.get_metrics()
        # Merge battery and fan rpm info
        bat = self.battery.get_battery_metrics()
        metrics["battery_pct"] = bat.get("battery_pct", 100.0)
        metrics["battery_health_pct"] = bat.get("battery_health_pct", 98.0)
        metrics["power_draw_watts"] = bat.get("power_draw_watts", 20.0)
        metrics["current_pwm"] = float(self.fan_controller.get_current_pwm())
        return metrics

    @sdbus.dbus_method(result_signature="s")
    def get_platform_profile(self) -> str:
        return self.platform_profile.get_current_profile()

    @sdbus.dbus_method(input_signature="s", result_signature="b")
    def set_platform_profile(self, profile: str) -> bool:
        return self.platform_profile.set_profile(profile)

    @sdbus.dbus_method(result_signature="as")
    def get_available_platform_profiles(self) -> List[str]:
        return self.platform_profile.get_supported_profiles()

    @sdbus.dbus_method(result_signature="s")
    def get_fan_mode(self) -> str:
        return self.fan_controller.get_mode()

    @sdbus.dbus_method(input_signature="s", result_signature="b")
    def set_fan_mode(self, mode: str) -> bool:
        return self.fan_controller.set_mode(mode)

    @sdbus.dbus_method(result_signature="a(dd)")
    def get_custom_fan_curve(self) -> List[Tuple[float, float]]:
        return self.fan_controller.get_curve()

    @sdbus.dbus_method(input_signature="a(dd)", result_signature="b")
    def set_custom_fan_curve(self, points: List[Tuple[float, float]]) -> bool:
        return self.fan_controller.set_curve(points)

    @sdbus.dbus_method(result_signature="a{ss}")
    def get_gpu_status(self) -> Dict[str, str]:
        st = self.gpu_switch.get_status()
        return {
            "current_mode": str(st.get("current_mode", "hybrid")),
            "pending_mode": str(st.get("pending_mode", "hybrid")),
            "requires_reboot": "true" if st.get("requires_reboot") else "false",
            "backend": str(st.get("backend", "simulated")),
        }

    @sdbus.dbus_method(input_signature="s", result_signature="b")
    def set_gpu_mode(self, mode: str) -> bool:
        return self.gpu_switch.set_gpu_mode(mode)

    @sdbus.dbus_method(result_signature="a{ss}")
    def get_undervolt_status(self) -> Dict[str, str]:
        return self.undervolt.get_status()

    @sdbus.dbus_method(input_signature="ii", result_signature="b")
    def set_undervolt_offset(self, core_mv: int, cache_mv: int) -> bool:
        return self.undervolt.set_undervolt_offset(core_mv, cache_mv)

    @sdbus.dbus_method(input_signature="ii", result_signature="b")
    def set_power_limits(self, pl1_w: int, pl2_w: int) -> bool:
        return self.undervolt.set_power_limits(pl1_w, pl2_w)

    @sdbus.dbus_method(result_signature="i")
    def get_battery_limit(self) -> int:
        return self.battery.get_charge_limit()

    @sdbus.dbus_method(input_signature="i", result_signature="b")
    def set_battery_limit(self, limit: int) -> bool:
        return self.battery.set_charge_limit(limit)

    @sdbus.dbus_method(input_signature="sasii", result_signature="b")
    def set_lighting(self, mode: str, zone_hex_colors: List[str], brightness: int, speed: int) -> bool:
        return self.lighting.set_lighting(mode, zone_hex_colors, brightness, speed)

    @sdbus.dbus_method(input_signature="bb", result_signature="b")
    def set_network_boost(self, enabled: bool, dual_force: bool) -> bool:
        return self.network_qos.set_network_boost(enabled, dual_force)

    @sdbus.dbus_method(result_signature="a{sb}")
    def get_network_boost_status(self) -> Dict[str, bool]:
        return self.network_qos.get_status()

    @sdbus.dbus_method(result_signature="a{ss}")
    def run_game_optimizer(self) -> Dict[str, str]:
        res = self.game_optimizer.optimize_system()
        return {
            "freed_mb": str(res.get("freed_mb", 0)),
            "governor": str(res.get("governor", "performance")),
            "boosted_pids": ",".join(res.get("boosted_pids", [])),
        }

    def start_services(self):
        self.hotkey_listener.start()

    def teardown(self):
        logger.info("Executing Nuxarchy Daemon teardown...")
        self.hotkey_listener.stop()
        self.fan_controller.teardown()
        self.network_qos.teardown()
        self.telemetry.stop()
        logger.info("Nuxarchy Daemon teardown finished.")


# Compatibility alias
NuxarchyDaemon = NuxarchyInterface


def run_daemon():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    # Require root if running on POSIX
    if hasattr(os, "geteuid") and os.geteuid() != 0:
        logger.critical("Fatal: Nuxarchy Daemon requires root privileges (UID 0).")
        sys.exit(1)

    logger.info("Initializing Nuxarchy Daemon on System Bus...")
    interface = NuxarchyInterface()

    def handle_signal(sig, frame):
        logger.info("Received signal %d, shutting down cleanly...", sig)
        interface.teardown()
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    if HAS_SDBUS:
        try:
            bus = sdbus.sd_bus_open_system()
            sdbus.set_default_bus(bus)
            sdbus.request_name(DBUS_SERVICE_NAME)
            interface.export_to_dbus(DBUS_OBJECT_PATH)
            logger.info("Nuxarchy Daemon successfully registered at %s on System Bus", DBUS_SERVICE_NAME)
        except Exception as e:
            logger.error("Failed to acquire System D-Bus: %s", e)
    else:
        logger.warning("sdbus C-library not available, operating in stand-alone test mode")

    interface.start_services()

    # Main service loop
    try:
        while True:
            time.sleep(1.0)
    except (KeyboardInterrupt, SystemExit):
        handle_signal(signal.SIGTERM, None)


if __name__ == "__main__":
    run_daemon()
