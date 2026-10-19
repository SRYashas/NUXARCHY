"""
OMEN Gaming Hub: Application Settings View
Configures telemetry refresh rates, temperature units, autostart, and profile persistence.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFrame, QLabel, QGridLayout, QComboBox,
    QCheckBox, QPushButton, QMessageBox, QHBoxLayout
)
from PySide6.QtCore import Qt

from nuxarchy.services.profile_manager import ProfileManager, AppSettings


class SettingsView(QWidget):
    def __init__(self, profile_mgr: ProfileManager, parent=None):
        super().__init__(parent)
        self.mgr = profile_mgr
        self.settings = profile_mgr.settings

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        # Header
        header = QVBoxLayout()
        title = QLabel("APPLICATION SETTINGS & PREFERENCES")
        title.setStyleSheet("color: #FFFFFF; font-size: 20px; font-weight: 800; letter-spacing: 1px;")
        header.addWidget(title)

        sub = QLabel("Customize hardware telemetry refresh intervals, temperature units, and desktop integration.")
        sub.setStyleSheet("color: #9CA3AF; font-size: 13px;")
        header.addWidget(sub)
        layout.addLayout(header)

        # General Settings Card
        card = QFrame()
        card.setProperty("class", "cardFrame")
        c_layout = QVBoxLayout(card)
        c_layout.setSpacing(16)

        c_title = QLabel("MONITORING & DISPLAY PREFERENCES")
        c_title.setProperty("class", "cardTitle")
        c_layout.addWidget(c_title)

        grid = QGridLayout()
        grid.setSpacing(14)

        # 1. Polling Interval
        grid.addWidget(QLabel("Telemetry Refresh Interval:"), 0, 0)
        self.combo_interval = QComboBox()
        self.combo_interval.addItems(["500 ms (Fast)", "1000 ms (Balanced - Recommended)", "2000 ms (Low CPU)"])
        curr_int = f"{self.settings.polling_interval_ms} ms"
        for i in range(self.combo_interval.count()):
            if str(self.settings.polling_interval_ms) in self.combo_interval.itemText(i):
                self.combo_interval.setCurrentIndex(i)
        grid.addWidget(self.combo_interval, 0, 1)

        # 2. Temperature Unit
        grid.addWidget(QLabel("Temperature Unit:"), 1, 0)
        self.combo_unit = QComboBox()
        self.combo_unit.addItems(["Celsius (°C)", "Fahrenheit (°F)"])
        self.combo_unit.setCurrentIndex(0 if self.settings.temperature_unit == "C" else 1)
        grid.addWidget(self.combo_unit, 1, 1)

        # 3. Checkboxes
        grid.addWidget(QLabel("System Startup:"), 2, 0)
        self.chk_minimized = QCheckBox("Start minimized to system tray")
        self.chk_minimized.setChecked(self.settings.start_minimized)
        grid.addWidget(self.chk_minimized, 2, 1)

        grid.addWidget(QLabel("Game Booster:"), 3, 0)
        self.chk_booster = QCheckBox("Automatically activate performance profile when launched games start")
        self.chk_booster.setChecked(self.settings.enable_auto_boost)
        grid.addWidget(self.chk_booster, 3, 1)

        c_layout.addLayout(grid)
        layout.addWidget(card)

        # Actions Row
        act_row = QHBoxLayout()
        btn_save = QPushButton("SAVE SETTINGS")
        btn_save.setProperty("class", "primaryButton")
        btn_save.clicked.connect(self._save_settings)
        act_row.addWidget(btn_save)

        btn_reset = QPushButton("Reset to Defaults")
        btn_reset.setProperty("class", "secondaryButton")
        btn_reset.clicked.connect(self._reset_defaults)
        act_row.addWidget(btn_reset)

        act_row.addStretch()
        layout.addLayout(act_row)
        layout.addStretch()

    def _save_settings(self):
        # Parse interval
        text = self.combo_interval.currentText()
        if "500" in text:
            self.settings.polling_interval_ms = 500
        elif "2000" in text:
            self.settings.polling_interval_ms = 2000
        else:
            self.settings.polling_interval_ms = 1000

        self.settings.temperature_unit = "C" if "Celsius" in self.combo_unit.currentText() else "F"
        self.settings.start_minimized = self.chk_minimized.isChecked()
        self.settings.enable_auto_boost = self.chk_booster.isChecked()

        if self.mgr.save_settings(self.settings):
            QMessageBox.information(self, "Settings Saved", "Preferences successfully updated.")
        else:
            QMessageBox.warning(self, "Save Error", "Failed to write configuration file.")

    def _reset_defaults(self):
        self.settings = AppSettings()
        self.mgr.save_settings(self.settings)
        self.combo_interval.setCurrentIndex(1)
        self.combo_unit.setCurrentIndex(0)
        self.chk_minimized.setChecked(False)
        self.chk_booster.setChecked(True)
        QMessageBox.information(self, "Settings Reset", "Restored factory defaults.")
