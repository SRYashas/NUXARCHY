"""
Network Throughput Telemetry Monitor
Calculates upload and download rates (KB/s, MB/s) by sampling delta bytes.
"""

import time
import os
from dataclasses import dataclass


@dataclass
class NetworkTelemetry:
    download_kbps: float = 0.0
    upload_kbps: float = 0.0
    total_received_mb: float = 0.0
    total_sent_mb: float = 0.0


class NetworkMonitor:
    def __init__(self):
        self._prev_time = time.time()
        self._prev_rx_bytes = 0
        self._prev_tx_bytes = 0
        self._init_baseline()

    def _init_baseline(self):
        rx, tx = self._read_bytes()
        self._prev_rx_bytes = rx
        self._prev_tx_bytes = tx
        self._prev_time = time.time()

    def _read_bytes(self) -> tuple:
        rx_total = 0
        tx_total = 0

        # Try /proc/net/dev on Linux
        if os.path.exists("/proc/net/dev"):
            try:
                with open("/proc/net/dev", "r") as f:
                    lines = f.readlines()[2:]  # Skip header lines
                for line in lines:
                    parts = line.strip().split()
                    if len(parts) >= 10:
                        iface = parts[0].strip(":")
                        if iface != "lo":  # Ignore loopback
                            rx_total += int(parts[1])
                            tx_total += int(parts[9])
                return rx_total, tx_total
            except Exception:
                pass

        # Fallback to psutil
        try:
            import psutil
            net = psutil.net_io_counters()
            return net.bytes_recv, net.bytes_sent
        except Exception:
            return 0, 0

    def sample(self) -> NetworkTelemetry:
        t = NetworkTelemetry()
        now = time.time()
        dt = max(0.001, now - self._prev_time)

        rx_curr, tx_curr = self._read_bytes()

        if self._prev_rx_bytes > 0:
            delta_rx = max(0, rx_curr - self._prev_rx_bytes)
            delta_tx = max(0, tx_curr - self._prev_tx_bytes)
            t.download_kbps = round((delta_rx / 1024.0) / dt, 1)
            t.upload_kbps = round((delta_tx / 1024.0) / dt, 1)

        t.total_received_mb = round(rx_curr / (1024 * 1024), 1)
        t.total_sent_mb = round(tx_curr / (1024 * 1024), 1)

        self._prev_rx_bytes = rx_curr
        self._prev_tx_bytes = tx_curr
        self._prev_time = now

        return t
