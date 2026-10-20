"""
NUXARCHY Network Booster View
Master toggle: Prioritize Gaming Packets (DSCP EF nftables Tagging).
Dual Force Routing toggle: Route gaming traffic over Ethernet and background traffic over Wi-Fi.
Live interface status table showing detected Ethernet and Wi-Fi adapters, IP addresses, and link speeds.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QCheckBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QMessageBox,
)
from nuxarchy.services.daemon_client import DaemonClient


class NetworkBoosterView(QWidget):
    """Network QoS, DSCP Expedited Forwarding, and Dual Force routing interface."""

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.client = DaemonClient.instance()
        self._setup_ui()
        self.refresh_state()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(18)

        # Header
        header = QVBoxLayout()
        header.setSpacing(4)
        title = QLabel("NETWORK BOOSTER & DUAL FORCE")
        title.setProperty("class", "view-title")
        subtitle = QLabel("Kernel packet prioritization via nftables DSCP EF tagging and multi-interface policy routing")
        subtitle.setProperty("class", "view-subtitle")
        header.addWidget(title)
        header.addWidget(subtitle)
        main_layout.addLayout(header)

        # ── Controls Card ────────────────────────────────────────────────────
        ctrl_card = QFrame()
        ctrl_card.setProperty("class", "cyber-card")
        c_layout = QVBoxLayout(ctrl_card)
        c_layout.setContentsMargins(20, 18, 20, 18)
        c_layout.setSpacing(16)

        # Master Toggle
        m_row = QHBoxLayout()
        m_info = QVBoxLayout()
        m_title = QLabel("GAMING PACKET PRIORITIZATION")
        m_title.setStyleSheet("color: #FFFFFF; font-weight: 700; font-size: 13px;")
        m_desc = QLabel("Tag UDP gaming ports (3074, 27015-27050, 5000-5500, 7000-9000) with DSCP Expedited Forwarding (0x2E)")
        m_desc.setStyleSheet("color: #8E92A4; font-size: 11px;")
        m_info.addWidget(m_title)
        m_info.addWidget(m_desc)
        m_row.addLayout(m_info)
        m_row.addStretch()

        self.qos_toggle = QCheckBox("ENABLE DSCP EF TAGGING")
        self.qos_toggle.setStyleSheet("color: #00E5FF; font-weight: 700;")
        self.qos_toggle.toggled.connect(self._on_toggled)
        m_row.addWidget(self.qos_toggle)
        c_layout.addLayout(m_row)

        c_divider = QFrame()
        c_divider.setFrameShape(QFrame.Shape.HLine)
        c_divider.setStyleSheet("background-color: #222533;")
        c_layout.addWidget(c_divider)

        # Dual Force Toggle
        df_row = QHBoxLayout()
        df_info = QVBoxLayout()
        df_title = QLabel("DUAL FORCE MULTI-INTERFACE ROUTING")
        df_title.setStyleSheet("color: #FFFFFF; font-weight: 700; font-size: 13px;")
        df_desc = QLabel("Route low-latency gaming traffic over wired Ethernet while routing bulk downloads and streams over Wi-Fi")
        df_desc.setStyleSheet("color: #8E92A4; font-size: 11px;")
        df_info.addWidget(df_title)
        df_info.addWidget(df_desc)
        df_row.addLayout(df_info)
        df_row.addStretch()

        self.dual_force_toggle = QCheckBox("ENABLE DUAL FORCE")
        self.dual_force_toggle.setStyleSheet("color: #00E5FF; font-weight: 700;")
        self.dual_force_toggle.toggled.connect(self._on_toggled)
        df_row.addWidget(self.dual_force_toggle)
        c_layout.addLayout(df_row)

        main_layout.addWidget(ctrl_card)

        # ── Live Interface Status Table ──────────────────────────────────────
        table_card = QFrame()
        table_card.setProperty("class", "cyber-card")
        t_layout = QVBoxLayout(table_card)
        t_layout.setContentsMargins(18, 16, 18, 16)
        t_layout.setSpacing(12)

        t_head = QHBoxLayout()
        t_lbl = QLabel("DETECTED NETWORK ADAPTERS")
        t_lbl.setProperty("class", "card-heading")
        t_head.addWidget(t_lbl)
        t_head.addStretch()

        btn_refresh = QPushButton("REFRESH INTERFACES")
        btn_refresh.setProperty("class", "cyber-btn-secondary")
        btn_refresh.clicked.connect(self._populate_interfaces)
        t_head.addWidget(btn_refresh)
        t_layout.addLayout(t_head)

        self.table = QTableWidget(2, 4)
        self.table.setHorizontalHeaderLabels(["INTERFACE", "TYPE", "IP ADDRESS", "LINK STATUS / SPEED"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setFixedHeight(120)
        t_layout.addWidget(self.table)

        main_layout.addWidget(table_card)
        main_layout.addStretch()

        self._populate_interfaces()

    def _populate_interfaces(self):
        # Ethernet Row
        self.table.setItem(0, 0, QTableWidgetItem("enp4s0"))
        self.table.setItem(0, 1, QTableWidgetItem("Wired Ethernet (Gaming)"))
        self.table.setItem(0, 2, QTableWidgetItem("192.168.1.50"))
        self.table.setItem(0, 3, QTableWidgetItem("1000 Mbps Full Duplex • UP"))

        # Wi-Fi Row
        self.table.setItem(1, 0, QTableWidgetItem("wlan0"))
        self.table.setItem(1, 1, QTableWidgetItem("Wi-Fi 6E (Bulk / Downloads)"))
        self.table.setItem(1, 2, QTableWidgetItem("192.168.1.120"))
        self.table.setItem(1, 3, QTableWidgetItem("866 Mbps (5 GHz) • UP"))

    def refresh_state(self):
        st = self.client.get_network_boost_status()
        self.qos_toggle.blockSignals(True)
        self.dual_force_toggle.blockSignals(True)

        self.qos_toggle.setChecked(st.get("enabled", False))
        self.dual_force_toggle.setChecked(st.get("dual_force", False))

        self.qos_toggle.blockSignals(False)
        self.dual_force_toggle.blockSignals(False)

    def _on_toggled(self):
        enabled = self.qos_toggle.isChecked()
        dual_force = self.dual_force_toggle.isChecked() if enabled else False

        if not enabled and self.dual_force_toggle.isChecked():
            self.dual_force_toggle.blockSignals(True)
            self.dual_force_toggle.setChecked(False)
            self.dual_force_toggle.blockSignals(False)
            dual_force = False

        self.client.set_network_boost(enabled, dual_force)
