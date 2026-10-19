"""
OMEN Gaming Hub: Thermal Management & Fan Control View
Monitors hardware temperatures, fan speeds (RPM), thermal limits, and maximum cooling boost.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QGridLayout, QProgressBar, QMessageBox
)
from PySide6.QtCore import Qt

from backend.capability import HardwareCapabilities
from backend.adapters.fan_controller import FanController
from backend.telemetry.system_monitor import SystemSnapshot


class ThermalView(QWidget):
    def __init__(self, caps: HardwareCapabilities, parent=None):
        super().__init__(parent)
        self.caps = caps
        self.controller = FanController()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Header
        header = QVBoxLayout()
        title = QLabel("THERMAL MANAGEMENT & COOLING")
        title.setStyleSheet("color: #FFFFFF; font-size: 20px; font-weight: 800; letter-spacing: 1px;")
        header.addWidget(title)

        sub = QLabel("Monitor CPU/GPU temperatures, fan telemetry, and switch between Auto and Max Cooling.")
        sub.setStyleSheet("color: #9CA3AF; font-size: 13px;")
        header.addWidget(sub)
        layout.addLayout(header)

        # Thermal Telemetry Cards
        grid = QGridLayout()
        grid.setSpacing(14)

        # CPU Temp Card
        self.card_cpu_temp = QFrame()
        self.card_cpu_temp.setProperty("class", "cardFrame")
        c_layout = QVBoxLayout(self.card_cpu_temp)
        c_title = QLabel("CPU PACKAGE TEMPERATURE")
        c_title.setProperty("class", "cardTitle")
        c_layout.addWidget(c_title)
        self.val_cpu_temp = QLabel("48°C")
        self.val_cpu_temp.setProperty("class", "cardValue")
        c_layout.addWidget(self.val_cpu_temp)
        self.bar_cpu_temp = QProgressBar()
        self.bar_cpu_temp.setRange(0, 105)
        self.bar_cpu_temp.setValue(48)
        c_layout.addWidget(self.bar_cpu_temp)
        self.sub_cpu_temp = QLabel("Throttle Limit: 100°C • Status: Optimal")
        self.sub_cpu_temp.setProperty("class", "cardSubtext")
        c_layout.addWidget(self.sub_cpu_temp)
        grid.addWidget(self.card_cpu_temp, 0, 0)

        # GPU Temp Card
        self.card_gpu_temp = QFrame()
        self.card_gpu_temp.setProperty("class", "cardFrame")
        g_layout = QVBoxLayout(self.card_gpu_temp)
        g_title = QLabel("NVIDIA RTX 4050 TEMPERATURE")
        g_title.setProperty("class", "cardTitle")
        g_layout.addWidget(g_title)
        self.val_gpu_temp = QLabel("52°C")
        self.val_gpu_temp.setProperty("class", "cardValue")
        g_layout.addWidget(self.val_gpu_temp)
        self.bar_gpu_temp = QProgressBar()
        self.bar_gpu_temp.setRange(0, 95)
        self.bar_gpu_temp.setValue(52)
        g_layout.addWidget(self.bar_gpu_temp)
        self.sub_gpu_temp = QLabel("Thermal Limit: 87°C • Status: Optimal")
        self.sub_gpu_temp.setProperty("class", "cardSubtext")
        g_layout.addWidget(self.sub_gpu_temp)
        grid.addWidget(self.card_gpu_temp, 0, 1)

        layout.addLayout(grid)

        # Fan Control Mode Card
        fan_card = QFrame()
        fan_card.setProperty("class", "cardFrame")
        f_layout = QVBoxLayout(fan_card)
        f_layout.setSpacing(14)

        f_title = QLabel("FAN SPEED & COOLING MODES")
        f_title.setProperty("class", "cardTitle")
        f_layout.addWidget(f_title)

        f_btn_layout = QHBoxLayout()
        f_btn_layout.setSpacing(12)

        self.btn_auto = QPushButton("AUTO COOLING\n(Firmware Dynamic Curve)")
        self.btn_auto.setProperty("class", "actionButton")
        self.btn_auto.setCheckable(True)
        self.btn_auto.setChecked(True)
        self.btn_auto.clicked.connect(lambda: self._set_fan_mode("auto"))
        f_btn_layout.addWidget(self.btn_auto)

        self.btn_max = QPushButton("MAXIMUM COOLING\n(Force 100% Fan RPM)")
        self.btn_max.setProperty("class", "actionButton")
        self.btn_max.setCheckable(True)
        self.btn_max.clicked.connect(lambda: self._set_fan_mode("max"))
        f_btn_layout.addWidget(self.btn_max)

        f_layout.addLayout(f_btn_layout)

        # RPM & Status
        self.lbl_fan_rpm = QLabel("Current Fan Speed: 2,450 RPM (Left & Right Turbines)")
        self.lbl_fan_rpm.setStyleSheet("color: #00FFD1; font-weight: 700; font-size: 13px;")
        f_layout.addWidget(self.lbl_fan_rpm)

        # Safety & Hardware Architecture Notice
        notice = QLabel(
            "SAFETY NOTICE: On HP OMEN laptops, baseline fan curves are governed by the Embedded Controller (EC) "
            "firmware to protect against hardware thermal runaway. 'Maximum Cooling' commands the firmware to boost fans "
            "to 100% duty cycle. Undocumented manual register tampering is blocked to prevent battery/VRM damage."
        )
        notice.setWordWrap(True)
        notice.setStyleSheet("color: #6B7280; font-size: 11px; margin-top: 6px;")
        f_layout.addWidget(notice)

        layout.addWidget(fan_card)
        layout.addStretch()

    def _set_fan_mode(self, mode: str):
        success, msg = self.controller.set_cooling_mode(mode)
        if success:
            self.btn_auto.setChecked(mode == "auto")
            self.btn_max.setChecked(mode == "max")
            self.lbl_fan_rpm.setText(f"Cooling Mode: {mode.upper()} • {msg}")
        else:
            QMessageBox.warning(self, "Fan Control", msg)

    def update_telemetry(self, snap: SystemSnapshot):
        cpu_t = snap.cpu.temperature_celsius or 0.0
        gpu_t = snap.gpu_nvidia.temperature_celsius or 0.0

        self.val_cpu_temp.setText(f"{cpu_t:.1f}°C")
        self.bar_cpu_temp.setValue(int(cpu_t))
        if cpu_t > 90:
            self.val_cpu_temp.setStyleSheet("color: #FF2A54;")
            self.sub_cpu_temp.setText("CAUTION: CPU Approaching Thermal Throttle Ceiling")
        else:
            self.val_cpu_temp.setStyleSheet("color: #FFFFFF;")
            self.sub_cpu_temp.setText("Throttle Limit: 100°C • Status: Optimal")

        self.val_gpu_temp.setText(f"{gpu_t:.1f}°C")
        self.bar_gpu_temp.setValue(int(gpu_t))
        if gpu_t > 82:
            self.val_gpu_temp.setStyleSheet("color: #FF2A54;")
            self.sub_gpu_temp.setText("CAUTION: GPU Running Hot")
        else:
            self.val_gpu_temp.setStyleSheet("color: #FFFFFF;")
            self.sub_gpu_temp.setText("Thermal Limit: 87°C • Status: Optimal")

        if snap.fan_rpm:
            self.lbl_fan_rpm.setText(f"Current Fan Speed: {snap.fan_rpm:,} RPM (Mode: {self.controller.get_current_mode().upper()})")
