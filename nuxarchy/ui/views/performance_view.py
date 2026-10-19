"""
NUXARCHY Hardware Center: Performance Control View
Features:
Power Mode with ECO, Balanced, Performance tiles,
Thermal Control with [MAX | AUTO | MANUAL] slider and live RPM readout,
and bottom System Temperature section (CPU, GPU, CPU Load).
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QComboBox, QMessageBox
)
from PySide6.QtCore import Qt

from nuxarchy.backend.capability import HardwareCapabilities
from nuxarchy.backend.adapters.platform_profile import PlatformProfileAdapter
from nuxarchy.backend.adapters.fan_controller import FanController
from nuxarchy.backend.telemetry.system_monitor import SystemSnapshot


class PerformanceView(QWidget):
    def __init__(self, caps: HardwareCapabilities, parent=None):
        super().__init__(parent)
        self.caps = caps
        self.profile_adapter = PlatformProfileAdapter()
        self.fan_controller = FanController()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 20, 28, 20)
        layout.setSpacing(24)

        # 1. Power Mode Header Row with dropdown & NUXARCHY Dynamic Power badge
        top_row = QHBoxLayout()
        lbl_power_mode = QLabel("Power Mode  ⓘ")
        lbl_power_mode.setStyleSheet("color: #FFFFFF; font-size: 15px; font-weight: 800; letter-spacing: 0.5px;")
        top_row.addWidget(lbl_power_mode)

        top_row.addStretch()

        # Dropdown
        combo_auto = QComboBox()
        combo_auto.addItems(["Auto Power Mode Settings", "Manual Power Mode"])
        combo_auto.setStyleSheet("""
            QComboBox {
                background-color: #12141A;
                color: #FFFFFF;
                border: 1px solid #232734;
                border-radius: 4px;
                padding: 5px 12px;
                font-size: 11px;
                font-weight: 600;
            }
        """)
        top_row.addWidget(combo_auto)

        # Dynamic Power Diamond Badge
        badge_box = QLabel("◆  Optimized with\n   NUXARCHY Dynamic Power")
        badge_box.setStyleSheet("color: #9CA3AF; font-size: 10px; font-weight: 700; margin-left: 12px;")
        top_row.addWidget(badge_box)

        layout.addLayout(top_row)

        # 2. Three Power Mode Cards (ECO, Balanced, Performance)
        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)

        # Card 1: ECO
        self.card_eco = self._build_mode_card("🌿\n\nECO", "eco", is_active=False)
        self.card_eco.mousePressEvent = lambda e: self._select_mode("quiet")
        cards_row.addWidget(self.card_eco)

        # Card 2: Balanced
        self.card_bal = self._build_mode_card("◇\n\nBalanced", "balanced", is_active=False)
        self.card_bal.mousePressEvent = lambda e: self._select_mode("balanced")
        cards_row.addWidget(self.card_bal)

        # Card 3: Performance (Active in Screenshot 3 with glowing border)
        self.card_perf = self._build_mode_card("📊\n\nPerformance", "performance", is_active=True)
        self.card_perf.mousePressEvent = lambda e: self._select_mode("performance")
        cards_row.addWidget(self.card_perf)

        layout.addLayout(cards_row)

        # 3. Thermal Control Section
        tc_title = QLabel("Thermal Control  ⓘ")
        tc_title.setStyleSheet("color: #FFFFFF; font-size: 15px; font-weight: 800; letter-spacing: 0.5px; margin-top: 10px;")
        layout.addWidget(tc_title)

        # Segmented pill slider: [ MAX | AUTO | MANUAL ]
        slider_frame = QHBoxLayout()
        self.tc_pill = QFrame()
        self.tc_pill.setStyleSheet("""
            QFrame {
                background-color: #161822;
                border-radius: 14px;
                border: 1px solid #282D3D;
                max-width: 220px;
            }
        """)
        tc_layout = QHBoxLayout(self.tc_pill)
        tc_layout.setContentsMargins(4, 4, 4, 4)
        tc_layout.setSpacing(2)

        self.btn_tc_max = QPushButton("🌀 MAX")
        self.btn_tc_max.setCheckable(True)
        self.btn_tc_max.setChecked(True)
        self.btn_tc_max.setStyleSheet(self._get_pill_btn_style(active=True))
        self.btn_tc_max.clicked.connect(lambda: self._set_thermal_mode("max"))
        tc_layout.addWidget(self.btn_tc_max)

        self.btn_tc_auto = QPushButton("AUTO")
        self.btn_tc_auto.setCheckable(True)
        self.btn_tc_auto.setStyleSheet(self._get_pill_btn_style(active=False))
        self.btn_tc_auto.clicked.connect(lambda: self._set_thermal_mode("auto"))
        tc_layout.addWidget(self.btn_tc_auto)

        self.btn_tc_man = QPushButton("MANUAL")
        self.btn_tc_man.setCheckable(True)
        self.btn_tc_man.setStyleSheet(self._get_pill_btn_style(active=False))
        self.btn_tc_man.clicked.connect(lambda: self._set_thermal_mode("manual"))
        tc_layout.addWidget(self.btn_tc_man)

        slider_frame.addStretch()
        slider_frame.addWidget(self.tc_pill)
        slider_frame.addStretch()
        layout.addLayout(slider_frame)

        # Readout: 6100 RPM Fan Speed (matches Screenshot 3)
        rpm_box = QVBoxLayout()
        rpm_box.setAlignment(Qt.AlignCenter)
        self.val_rpm = QLabel("6100 RPM")
        self.val_rpm.setStyleSheet("color: #FFFFFF; font-size: 26px; font-weight: 800; letter-spacing: 1px;")
        self.val_rpm.setAlignment(Qt.AlignCenter)
        rpm_box.addWidget(self.val_rpm)

        lbl_fan_speed = QLabel("Fan Speed")
        lbl_fan_speed.setStyleSheet("color: #9CA3AF; font-size: 11px; font-weight: 600;")
        lbl_fan_speed.setAlignment(Qt.AlignCenter)
        rpm_box.addWidget(lbl_fan_speed)
        layout.addLayout(rpm_box)

        layout.addSpacing(20)

        # 4. System Temperature Section (Bottom of Screenshot 3)
        temp_sec_title = QLabel("System Temperature")
        temp_sec_title.setStyleSheet("color: #FFFFFF; font-size: 15px; font-weight: 800; letter-spacing: 0.5px;")
        layout.addWidget(temp_sec_title)

        temp_row = QHBoxLayout()
        temp_row.setSpacing(40)

        # Metric 1: CPU Temperature (89°C in #00FF85)
        col1 = QVBoxLayout()
        self.val_cpu_temp = QLabel("89°C")
        self.val_cpu_temp.setStyleSheet("color: #00FF85; font-size: 32px; font-weight: 900;")
        col1.addWidget(self.val_cpu_temp)
        lbl_ct = QLabel("CPU Temperature")
        lbl_ct.setStyleSheet("color: #9CA3AF; font-size: 12px; font-weight: 600;")
        col1.addWidget(lbl_ct)
        temp_row.addLayout(col1)

        # Metric 2: GPU Temperature (55°C in #00FF85)
        col2 = QVBoxLayout()
        self.val_gpu_temp = QLabel("55°C")
        self.val_gpu_temp.setStyleSheet("color: #00FF85; font-size: 32px; font-weight: 900;")
        col2.addWidget(self.val_gpu_temp)
        lbl_gt = QLabel("GPU Temperature")
        lbl_gt.setStyleSheet("color: #9CA3AF; font-size: 12px; font-weight: 600;")
        col2.addWidget(lbl_gt)
        temp_row.addLayout(col2)

        # Metric 3: CPU Utilization (66% in White)
        col3 = QVBoxLayout()
        self.val_cpu_util = QLabel("66%")
        self.val_cpu_util.setStyleSheet("color: #FFFFFF; font-size: 32px; font-weight: 900;")
        col3.addWidget(self.val_cpu_util)
        lbl_cu = QLabel("CPU Utilization")
        lbl_cu.setStyleSheet("color: #9CA3AF; font-size: 12px; font-weight: 600;")
        col3.addWidget(lbl_cu)
        temp_row.addLayout(col3)

        temp_row.addStretch()
        layout.addLayout(temp_row)
        layout.addStretch()

    def _build_mode_card(self, label_text: str, mode_id: str, is_active: bool) -> QFrame:
        card = QFrame()
        card.setMinimumHeight(130)
        card.setCursor(Qt.PointingHandCursor)
        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignCenter)

        lbl = QLabel(label_text)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: 800; line-height: 1.4;")
        layout.addWidget(lbl)

        card.mode_id = mode_id
        card.lbl = lbl
        self._set_card_active_style(card, is_active)
        return card

    def _set_card_active_style(self, card: QFrame, is_active: bool):
        if is_active:
            # Glowing pink/orange border identical to Screenshot 3
            card.setStyleSheet("""
                QFrame {
                    background-color: #161822;
                    border: 2px solid #FF2A54;
                    border-radius: 8px;
                }
            """)
        else:
            card.setStyleSheet("""
                QFrame {
                    background-color: #12141A;
                    border: 1px solid #1E222D;
                    border-radius: 8px;
                }
                QFrame:hover {
                    border: 1px solid #30374A;
                }
            """)

    def _get_pill_btn_style(self, active: bool) -> str:
        if active:
            return """
                QPushButton {
                    background-color: #55B5E6;
                    color: #000000;
                    font-size: 11px;
                    font-weight: 800;
                    border-radius: 12px;
                    padding: 5px 12px;
                    border: none;
                }
            """
        else:
            return """
                QPushButton {
                    background-color: transparent;
                    color: #9CA3AF;
                    font-size: 11px;
                    font-weight: 700;
                    border-radius: 12px;
                    padding: 5px 12px;
                    border: none;
                }
            """

    def _select_mode(self, mode: str):
        success, msg = self.profile_adapter.set_profile(mode)
        if success:
            c = mode.lower()
            self._set_card_active_style(self.card_eco, c in ["quiet", "eco"])
            self._set_card_active_style(self.card_bal, c in ["balanced", "default"])
            self._set_card_active_style(self.card_perf, c in ["performance", "extreme"])

    def _set_thermal_mode(self, mode: str):
        self.btn_tc_max.setChecked(mode == "max")
        self.btn_tc_auto.setChecked(mode == "auto")
        self.btn_tc_man.setChecked(mode == "manual")

        self.btn_tc_max.setStyleSheet(self._get_pill_btn_style(mode == "max"))
        self.btn_tc_auto.setStyleSheet(self._get_pill_btn_style(mode == "auto"))
        self.btn_tc_man.setStyleSheet(self._get_pill_btn_style(mode == "manual"))

        self.fan_controller.set_cooling_mode("max" if mode == "max" else "auto")
        self.val_rpm.setText("6100 RPM" if mode == "max" else "2450 RPM")

    def update_telemetry(self, snap: SystemSnapshot):
        if snap.cpu.temperature_celsius is not None:
            self.val_cpu_temp.setText(f"{snap.cpu.temperature_celsius:.0f}°C")
        if snap.gpu_nvidia.temperature_celsius is not None:
            self.val_gpu_temp.setText(f"{snap.gpu_nvidia.temperature_celsius:.0f}°C")
        self.val_cpu_util.setText(f"{snap.cpu.total_utilization:.0f}%")
        if snap.fan_rpm:
            self.val_rpm.setText(f"{snap.fan_rpm:,} RPM")
