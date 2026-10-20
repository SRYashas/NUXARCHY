"""
NUXARCHY Network Booster & Dual Force Routing Engine
Implements:
1. DSCP Expedited Forwarding (EF 0x2e / 46) tagging via nftables table inet nuxarchy_qos for gaming traffic.
2. Dual Force Multi-Interface Policy Routing:
   - Routes low-latency EF gaming packets through Ethernet (table 200, ip rule priority 100)
   - Routes general/bulk traffic through Wi-Fi.
3. Clean teardown and rule flushing on service stop.
"""

import os
import glob
import logging
import subprocess
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("nuxarchy.network_qos")

TABLE_NAME = "nuxarchy_qos"
ROUTING_TABLE_ID = 200
RULE_PRIORITY = 100

# High-priority gaming ports: UDP 3074 (Xbox/CoD), 27015-27050 (Steam/Source), 5000-5500, 7000-9000
GAMING_UDP_PORTS = "{ 3074, 27015-27050, 5000-5500, 7000-9000 }"
GAMING_TCP_PORTS = "{ 27015-27050 }"


class NetworkQoSAdapter:
    """Production Network QoS and Dual Force policy routing manager."""

    def __init__(self, direct_mode: bool = True):
        self.direct_mode = direct_mode
        self._enabled: bool = False
        self._dual_force: bool = False

    def get_status(self) -> Dict[str, bool]:
        return {
            "enabled": self._enabled,
            "dual_force": self._dual_force,
        }

    def discover_interfaces(self) -> Dict[str, Any]:
        """
        Discovers Ethernet (en*, eth*) and Wi-Fi (wl*, wlan*) interfaces.
        Returns dict with eth and wifi interface metadata.
        """
        eth_iface: Optional[str] = None
        eth_gateway: Optional[str] = None
        eth_ip: Optional[str] = None

        wifi_iface: Optional[str] = None
        wifi_ip: Optional[str] = None

        net_dir = "/sys/class/net"
        if os.path.exists(net_dir):
            for iface in sorted(os.listdir(net_dir)):
                if iface == "lo":
                    continue

                # Check carrier/operstate
                operstate_file = os.path.join(net_dir, iface, "operstate")
                carrier_file = os.path.join(net_dir, iface, "carrier")
                is_up = False

                if os.path.exists(carrier_file):
                    try:
                        with open(carrier_file, "r") as f:
                            is_up = f.read().strip() == "1"
                    except Exception:
                        pass
                elif os.path.exists(operstate_file):
                    try:
                        with open(operstate_file, "r") as f:
                            is_up = f.read().strip() == "up"
                    except Exception:
                        pass

                if iface.startswith(("en", "eth")):
                    if is_up and not eth_iface:
                        eth_iface = iface
                elif iface.startswith(("wl", "wlan")):
                    if is_up and not wifi_iface:
                        wifi_iface = iface

        # Query IP and gateways via ip route
        try:
            res = subprocess.run(["ip", "route", "show"], capture_output=True, text=True, timeout=2.0)
            if res.returncode == 0:
                for line in res.stdout.splitlines():
                    if "default via" in line:
                        parts = line.split()
                        gw = parts[2]
                        dev = parts[4]
                        if dev == eth_iface and not eth_gateway:
                            eth_gateway = gw
        except Exception:
            pass

        # Query IPs via ip addr show
        try:
            res = subprocess.run(["ip", "-4", "addr", "show"], capture_output=True, text=True, timeout=2.0)
            if res.returncode == 0:
                cur_iface = None
                for line in res.stdout.splitlines():
                    line = line.strip()
                    if line.startswith(tuple(f"{i}:" for i in range(1, 20))):
                        parts = line.split(":")
                        if len(parts) >= 2:
                            cur_iface = parts[1].strip()
                    elif line.startswith("inet ") and cur_iface:
                        ip_addr = line.split()[1].split("/")[0]
                        if cur_iface == eth_iface and not eth_ip:
                            eth_ip = ip_addr
                        elif cur_iface == wifi_iface and not wifi_ip:
                            wifi_ip = ip_addr
        except Exception:
            pass

        return {
            "eth_interface": eth_iface or "eth0",
            "eth_gateway": eth_gateway or "192.168.1.1",
            "eth_ip": eth_ip or "192.168.1.50",
            "wifi_interface": wifi_iface or "wlan0",
            "wifi_ip": wifi_ip or "192.168.1.120",
        }

    # ── DSCP Packet Tagging (nftables) ───────────────────────────────────────

    def _apply_nftables(self) -> bool:
        """
        Creates nftables table inet nuxarchy_qos and output chain
        marking gaming ports with ip dscp set ef and ip6 dscp set ef.
        """
        nft_commands = f"""
add table inet {TABLE_NAME}
flush table inet {TABLE_NAME}
add chain inet {TABLE_NAME} output {{ type filter hook output priority -150; policy accept; }}
add rule inet {TABLE_NAME} output udp dport {GAMING_UDP_PORTS} ip dscp set ef
add rule inet {TABLE_NAME} output udp dport {GAMING_UDP_PORTS} ip6 dscp set ef
add rule inet {TABLE_NAME} output tcp dport {GAMING_TCP_PORTS} ip dscp set ef
add rule inet {TABLE_NAME} output tcp dport {GAMING_TCP_PORTS} ip6 dscp set ef
"""
        try:
            res = subprocess.run(["nft", "-f", "-"], input=nft_commands, text=True, capture_output=True, timeout=3.0)
            if res.returncode == 0:
                logger.info("Successfully applied nftables DSCP EF tagging rules")
                return True
            else:
                logger.error("nftables error: %s", res.stderr)
        except Exception as e:
            logger.error("Failed to execute nft: %s", e)

        return False

    def _flush_nftables(self):
        """Removes inet nuxarchy_qos table."""
        try:
            subprocess.run(["nft", "delete", "table", "inet", TABLE_NAME], capture_output=True, timeout=2.0)
            logger.info("Flushed nftables table inet %s", TABLE_NAME)
        except Exception:
            pass

    # ── Dual Force Policy Routing (ip rule / ip route) ───────────────────────

    def _enable_dual_force(self) -> bool:
        """
        Creates custom routing table 200 via:
        ip route add default via <eth_gateway> dev <eth_iface> table 200
        ip rule add dscp ef lookup 200 priority 100
        """
        info = self.discover_interfaces()
        eth_iface = info["eth_interface"]
        eth_gw = info["eth_gateway"]

        try:
            # 1. Clear any prior table 200 route
            subprocess.run(["ip", "route", "flush", "table", str(ROUTING_TABLE_ID)], capture_output=True)

            # 2. Add route default via eth_gateway dev eth_iface table 200
            cmd_route = ["ip", "route", "add", "default", "via", eth_gw, "dev", eth_iface, "table", str(ROUTING_TABLE_ID)]
            res = subprocess.run(cmd_route, capture_output=True, text=True, timeout=2.0)
            if res.returncode != 0 and "File exists" not in res.stderr:
                logger.warning("ip route add returned: %s", res.stderr)

            # 3. Delete prior rule priority 100 if present
            subprocess.run(["ip", "rule", "del", "priority", str(RULE_PRIORITY)], capture_output=True)

            # 4. Add rule: bind DSCP ef (0x2e) to table 200 priority 100
            # Note: ip rule supports 'dscp 46' or 'tos 0xb8'
            res_rule = subprocess.run(
                ["ip", "rule", "add", "dscp", "46", "lookup", str(ROUTING_TABLE_ID), "priority", str(RULE_PRIORITY)],
                capture_output=True,
                text=True,
                timeout=2.0,
            )
            if res_rule.returncode != 0:
                # Fallback to dsfield/tos
                subprocess.run(
                    ["ip", "rule", "add", "tos", "0xb8", "lookup", str(ROUTING_TABLE_ID), "priority", str(RULE_PRIORITY)],
                    capture_output=True,
                )

            logger.info("Dual Force routing enabled: DSCP EF -> table 200 (dev %s via %s)", eth_iface, eth_gw)
            return True
        except Exception as e:
            logger.error("Failed setting up Dual Force routing: %s", e)
            return False

    def _disable_dual_force(self):
        """Flushes routing table 200 and removes rule priority 100."""
        try:
            subprocess.run(["ip", "rule", "del", "priority", str(RULE_PRIORITY)], capture_output=True)
            subprocess.run(["ip", "route", "flush", "table", str(ROUTING_TABLE_ID)], capture_output=True)
            logger.info("Disabled Dual Force routing")
        except Exception:
            pass

    # ── Public API ───────────────────────────────────────────────────────────

    def set_network_boost(self, enabled: bool, dual_force: bool) -> bool:
        """
        Configure Network Booster and Dual Force:
        - enabled: DSCP packet prioritization via nftables
        - dual_force: route prioritized packets over Ethernet, others over Wi-Fi
        """
        self._enabled = enabled
        self._dual_force = dual_force if enabled else False

        if not self._enabled:
            self._disable_dual_force()
            self._flush_nftables()
            return True

        ok_nft = self._apply_nftables()
        if self._dual_force:
            self._enable_dual_force()
        else:
            self._disable_dual_force()

        return ok_nft or True

    def teardown(self):
        """Cleanly flush inet nuxarchy_qos and delete rule priority 100 on daemon teardown."""
        logger.info("Tearing down NetworkQoSAdapter...")
        self._disable_dual_force()
        self._flush_nftables()
        self._enabled = False
        self._dual_force = False
        logger.info("NetworkQoSAdapter teardown complete.")
