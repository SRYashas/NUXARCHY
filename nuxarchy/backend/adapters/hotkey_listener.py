"""
NUXARCHY HP OMEN Physical Key Listener
Monitors /dev/input/event* and /dev/input/by-path/* for HP OMEN dedicated gaming hub keys
(KEY_PROG1 / 148, KEY_FAVORITES / 0x16c, or HP WMI event 0x21a9) using non-blocking event loops.
Invokes callback to fire the D-Bus omen_hotkey_pressed() signal.
"""

import os
import glob
import select
import struct
import logging
import threading
from typing import Callable, Optional, List

logger = logging.getLogger("nuxarchy.hotkey_listener")

# Linux input_event constants
EV_KEY = 0x01
KEY_PROG1 = 148
KEY_FAVORITES = 0x16C
OMEN_WMI_SCANCODE = 0x21A9

TARGET_DEVICE_SUBSTRINGS = (
    "hp wmi hotkeys",
    "at translated set 2 keyboard",
    "hp wireless hotkeys",
    "omen",
)

# Linux 64-bit input_event struct (24 bytes): timeval (8B + 8B), __u16 type (2B), __u16 code (2B), __s32 value (4B)
INPUT_EVENT_FORMAT = "qqHHi"
INPUT_EVENT_SIZE = 24


class HotkeyListener:
    """Production non-blocking Linux input_event listener for HP OMEN hardware keys."""

    def __init__(self, on_hotkey: Optional[Callable[[], None]] = None):
        self.on_hotkey = on_hotkey
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._open_fds: List[int] = []

    def start(self):
        """Start listening for OMEN key presses in a background thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True, name="OMENHotkeyListener")
        self._thread.start()
        logger.info("OMEN Hotkey Listener started")

    def stop(self):
        self._running = False
        for fd in self._open_fds:
            try:
                os.close(fd)
            except Exception:
                pass
        self._open_fds.clear()
        if self._thread and self._thread.is_alive():
            if threading.current_thread() != self._thread:
                self._thread.join(timeout=1.0)
        self._thread = None
        logger.info("OMEN Hotkey Listener stopped")

    def _discover_input_devices(self) -> List[str]:
        """Scan /dev/input/event* and /sys/class/input/event*/device/name."""
        matched_devs: List[str] = []
        event_paths = sorted(glob.glob("/dev/input/event*"))

        for dev_path in event_paths:
            base_name = os.path.basename(dev_path)
            sys_name_path = f"/sys/class/input/{base_name}/device/name"
            dev_name = ""
            if os.path.exists(sys_name_path):
                try:
                    with open(sys_name_path, "r") as f:
                        dev_name = f.read().strip().lower()
                except Exception:
                    pass

            if any(sub in dev_name for sub in TARGET_DEVICE_SUBSTRINGS):
                matched_devs.append(dev_path)

        return matched_devs

    def _listen_loop(self):
        devices = self._discover_input_devices()
        if not devices:
            logger.info("No matching HP keyboard input devices found on /dev/input (will retry periodically)")

        self._open_fds.clear()
        for d in devices:
            try:
                fd = os.open(d, os.O_RDONLY | os.O_NONBLOCK)
                self._open_fds.append(fd)
            except Exception as e:
                logger.debug("Could not open %s: %s", d, e)

        while self._running:
            if not self._open_fds:
                # Retry discovery every 5 seconds
                threading.Event().wait(5.0)
                devices = self._discover_input_devices()
                for d in devices:
                    try:
                        fd = os.open(d, os.O_RDONLY | os.O_NONBLOCK)
                        self._open_fds.append(fd)
                    except Exception:
                        pass
                continue

            try:
                # select with 1s timeout to check self._running flag
                r, _, _ = select.select(self._open_fds, [], [], 1.0)
                for fd in r:
                    try:
                        data = os.read(fd, INPUT_EVENT_SIZE)
                        if len(data) == INPUT_EVENT_SIZE:
                            tv_sec, tv_usec, ev_type, code, value = struct.unpack(INPUT_EVENT_FORMAT, data)
                            if ev_type == EV_KEY and value == 1:  # Key press event
                                if code in (KEY_PROG1, KEY_FAVORITES, OMEN_WMI_SCANCODE):
                                    logger.info("OMEN Key pressed! code=0x%X (%d)", code, code)
                                    if self.on_hotkey:
                                        self.on_hotkey()
                    except (BlockingIOError, OSError):
                        pass
            except Exception as e:
                logger.debug("Exception in hotkey select loop: %s", e)
