"""
NUXARCHY OMEN Light Studio & RGB Controller
Dual-Engine RGB implementation:
1. Engine 1: Direct HP WMI / Kernel Multicolor LED Sysfs (/sys/class/leds/hp::kbd_backlight/ or hp::kbd_zoned_backlight-*/)
2. Engine 2: OpenRGB Raw TCP SDK Client (127.0.0.1:6742) using exact 16-byte header struct.pack('<4sIII', b'ORGB', dev_idx, pkt_id, size)
3. Integrated Software Animation Loop for Static, Breathing, Color Cycle, and Wave across 4 zones.
"""

import os
import glob
import math
import time
import struct
import socket
import logging
import threading
from typing import List, Tuple, Optional, Dict, Any

logger = logging.getLogger("nuxarchy.lighting")

# OpenRGB Protocol Constants
OPENRGB_MAGIC = b"ORGB"
OPENRGB_DEFAULT_HOST = "127.0.0.1"
OPENRGB_DEFAULT_PORT = 6742

NET_PACKET_ID_REQUEST_CONTROLLER_COUNT = 0
NET_PACKET_ID_REQUEST_CONTROLLER_DATA = 1
NET_PACKET_ID_RGBCONTROLLER_UPDATELEDS = 1050
NET_PACKET_ID_RGBCONTROLLER_UPDATEZONELEDS = 1051
NET_PACKET_ID_RGBCONTROLLER_UPDATEMODE = 1101


def hex_to_rgb(hex_code: str) -> Tuple[int, int, int]:
    """Convert hex string (e.g. '#00E5FF') to (R, G, B) tuple."""
    h = hex_code.strip().lstrip("#")
    if len(h) == 6:
        try:
            return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        except ValueError:
            pass
    return 0, 229, 255


def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}"


class LightingAdapter:
    """Production Lighting Controller supporting HP WMI sysfs, OpenRGB raw TCP, and software effects."""

    def __init__(self, direct_mode: bool = True):
        self.direct_mode = direct_mode

        # Active state
        self._mode: str = "static"
        self._zone_colors: List[str] = ["#00E5FF", "#00E5FF", "#FF0552", "#FF0552"]  # 4 Zones
        self._brightness: int = 100  # 0..100
        self._speed: int = 50       # 1..100

        # Animation thread
        self._anim_running: bool = False
        self._anim_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Sysfs LED paths
        self._sysfs_multi_paths: List[str] = []
        self._sysfs_brightness_paths: List[str] = []
        self._discover_sysfs_leds()

    def _discover_sysfs_leds(self):
        """Locate HP WMI and kernel multicolor backlight paths."""
        self._sysfs_multi_paths.clear()
        self._sysfs_brightness_paths.clear()

        search_patterns = [
            "/sys/class/leds/hp::kbd_backlight*",
            "/sys/class/leds/hp::kbd_zoned_backlight*",
            "/sys/class/leds/*::kbd_backlight*",
            "/sys/class/leds/*multicolor*",
        ]
        for pattern in search_patterns:
            for d in glob.glob(pattern):
                multi_file = os.path.join(d, "multi_intensity")
                bright_file = os.path.join(d, "brightness")
                if os.path.exists(multi_file):
                    self._sysfs_multi_paths.append(multi_file)
                if os.path.exists(bright_file):
                    self._sysfs_brightness_paths.append(bright_file)

        logger.info(
            "Discovered %d sysfs multicolor paths, %d brightness paths",
            len(self._sysfs_multi_paths),
            len(self._sysfs_brightness_paths),
        )

    # ── Engine 1: Direct HP WMI / Kernel Sysfs ───────────────────────────────

    def _apply_sysfs_colors(self, rgb_list: List[Tuple[int, int, int]], brightness_pct: int):
        """Write colors directly to sysfs multicolor files."""
        scaled_brightness = max(0, min(255, int((brightness_pct / 100.0) * 255)))

        for b_path in self._sysfs_brightness_paths:
            try:
                with open(b_path, "w") as f:
                    f.write(str(scaled_brightness))
            except Exception:
                pass

        for m_path in self._sysfs_multi_paths:
            try:
                # Format: space-separated RGB integers (e.g., '255 0 82')
                # If 4 zones supported, concatenate or write primary
                line_parts = []
                for r, g, b in rgb_list:
                    line_parts.extend([str(r), str(g), str(b)])
                payload = " ".join(line_parts) + "\n"
                with open(m_path, "w") as f:
                    f.write(payload)
            except Exception:
                pass

    # ── Engine 2: OpenRGB Raw TCP SDK Client ─────────────────────────────────

    def _openrgb_send_colors(self, rgb_list: List[Tuple[int, int, int]]) -> bool:
        """
        Sends NET_PACKET_ID_RGBCONTROLLER_UPDATELEDS via OpenRGB TCP protocol.
        Header: struct.pack('<4sIII', b'ORGB', dev_idx, pkt_id, size)
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        try:
            sock.connect((OPENRGB_DEFAULT_HOST, OPENRGB_DEFAULT_PORT))

            # Request controller count to verify connection
            header_count = struct.pack("<4sIII", OPENRGB_MAGIC, 0, NET_PACKET_ID_REQUEST_CONTROLLER_COUNT, 0)
            sock.sendall(header_count)
            resp_header = sock.recv(16)
            if len(resp_header) < 16:
                sock.close()
                return False

            magic, dev_idx, pkt_id, size = struct.unpack("<4sIII", resp_header)
            if magic != OPENRGB_MAGIC:
                sock.close()
                return False

            resp_data = sock.recv(size) if size > 0 else b""
            if len(resp_data) >= 4:
                controller_count = struct.unpack("<I", resp_data[:4])[0]
            else:
                controller_count = 1

            # Send update to all controllers
            for c_idx in range(controller_count):
                led_data = bytearray()
                for r, g, b in rgb_list:
                    led_data.extend(struct.pack("BBBB", r, g, b, 0))

                # Payload: <I data_size + <H led_count + led_data
                payload = struct.pack("<IH", len(led_data) + 6, len(rgb_list)) + bytes(led_data)
                update_header = struct.pack(
                    "<4sIII",
                    OPENRGB_MAGIC,
                    c_idx,
                    NET_PACKET_ID_RGBCONTROLLER_UPDATELEDS,
                    len(payload),
                )
                sock.sendall(update_header + payload)

            sock.close()
            return True
        except Exception:
            return False

    # ── Hardware Dispatch ────────────────────────────────────────────────────

    def _dispatch_rgb(self, rgb_list: List[Tuple[int, int, int]], brightness_pct: int):
        # 1. Scale with brightness
        b_factor = max(0.0, min(1.0, brightness_pct / 100.0))
        scaled_rgbs = [
            (int(round(r * b_factor)), int(round(g * b_factor)), int(round(b * b_factor)))
            for r, g, b in rgb_list
        ]

        # 2. Try sysfs
        self._apply_sysfs_colors(scaled_rgbs, brightness_pct)

        # 3. Try OpenRGB SDK
        self._openrgb_send_colors(scaled_rgbs)

    # ── Animation Loop ───────────────────────────────────────────────────────

    def _start_animation_thread(self):
        if not self._anim_running:
            self._anim_running = True
            self._anim_thread = threading.Thread(target=self._animation_loop, daemon=True, name="LightingAnim")
            self._anim_thread.start()

    def _stop_animation_thread(self):
        self._anim_running = False
        if self._anim_thread and self._anim_thread.is_alive():
            if threading.current_thread() != self._anim_thread:
                self._anim_thread.join(timeout=1.0)
        self._anim_thread = None

    def _animation_loop(self):
        """Executes Breathing, Color Cycle, and Wave animation patterns."""
        step = 0.0
        while self._anim_running:
            try:
                with self._lock:
                    mode = self._mode
                    base_rgbs = [hex_to_rgb(h) for h in self._zone_colors]
                    brightness = self._brightness
                    speed = self._speed

                if mode == "breathing":
                    # Sine wave on brightness (0.1 to 1.0)
                    breath = (math.sin(step) + 1.0) / 2.0  # 0.0 .. 1.0
                    b_eff = int(brightness * (0.1 + 0.9 * breath))
                    self._dispatch_rgb(base_rgbs, b_eff)

                elif mode == "color_cycle":
                    # Rainbow hue cycle
                    hue = (step / (2 * math.pi)) % 1.0
                    r, g, b = self._hsv_to_rgb(hue, 1.0, 1.0)
                    cycle_rgbs = [(r, g, b)] * 4
                    self._dispatch_rgb(cycle_rgbs, brightness)

                elif mode == "wave":
                    # Phase-shifted wave across 4 zones
                    wave_rgbs = []
                    for z in range(4):
                        phase = step + (z * 0.8)
                        factor = (math.sin(phase) + 1.0) / 2.0
                        br, bg, bb = base_rgbs[z % len(base_rgbs)]
                        wave_rgbs.append((
                            int(round(br * factor)),
                            int(round(bg * factor)),
                            int(round(bb * factor)),
                        ))
                    self._dispatch_rgb(wave_rgbs, brightness)

                elif mode == "off":
                    self._dispatch_rgb([(0, 0, 0)] * 4, 0)
                    break
                else:  # static
                    self._dispatch_rgb(base_rgbs, brightness)
                    break

                # Speed scaling
                step_inc = 0.05 + (speed / 100.0) * 0.2
                step += step_inc
                time.sleep(0.04)  # ~25 FPS animation rate
            except Exception as e:
                logger.error("Error in lighting animation loop: %s", e)
                time.sleep(0.1)

    @staticmethod
    def _hsv_to_rgb(h: float, s: float, v: float) -> Tuple[int, int, int]:
        i = int(h * 6.0)
        f = (h * 6.0) - i
        p = v * (1.0 - s)
        q = v * (1.0 - s * f)
        t = v * (1.0 - s * (1.0 - f))
        i %= 6
        if i == 0:
            r, g, b = v, t, p
        elif i == 1:
            r, g, b = q, v, p
        elif i == 2:
            r, g, b = p, v, t
        elif i == 3:
            r, g, b = p, q, v
        elif i == 4:
            r, g, b = t, p, v
        else:
            r, g, b = v, p, q
        return int(r * 255), int(g * 255), int(b * 255)

    # ── Public API ───────────────────────────────────────────────────────────

    def set_lighting(self, mode: str, zone_hex_colors: List[str], brightness: int, speed: int) -> bool:
        """
        Configure lighting across 4 keyboard zones:
        - mode: "static", "breathing", "color_cycle", "wave", "off"
        - zone_hex_colors: list of 4 hex strings
        - brightness: 0..100
        - speed: 1..100
        """
        mode = mode.lower()
        if mode not in ("static", "breathing", "color_cycle", "wave", "off"):
            logger.error("Invalid lighting mode: %s", mode)
            return False

        with self._lock:
            self._mode = mode
            if zone_hex_colors and len(zone_hex_colors) >= 4:
                self._zone_colors = list(zone_hex_colors[:4])
            self._brightness = max(0, min(100, int(brightness)))
            self._speed = max(1, min(100, int(speed)))

        if mode in ("breathing", "color_cycle", "wave"):
            self._start_animation_thread()
        else:
            self._stop_animation_thread()
            if mode == "off":
                self._dispatch_rgb([(0, 0, 0)] * 4, 0)
            else:  # static
                rgbs = [hex_to_rgb(h) for h in self._zone_colors]
                self._dispatch_rgb(rgbs, self._brightness)

        logger.info("Applied lighting mode '%s' (brightness=%d%%, speed=%d)", mode, self._brightness, self._speed)
        return True

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "mode": self._mode,
                "zone_colors": list(self._zone_colors),
                "brightness": self._brightness,
                "speed": self._speed,
            }
