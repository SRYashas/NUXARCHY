"""
NUXARCHY Thermal & Fans View
Mode selector pills: [ AUTO (BIOS EC) ], [ MAX TURBO (100% RPM) ], [ CUSTOM CURVE ].
Embeds FanCurveEditor widget in the center.
Preset curve buttons: Silent, Balanced, Aggressive Gaming, and [ APPLY CURVE ].
"""

from typing import List, Tuple
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QPushButton,
    QMessageBox,
)
from nuxarchy.ui.widgets.fan_curve_editor import FanCurveEditor
from nuxarchy.services.daemon_client import DaemonClient

PRESET_SILENT = [(35.0, 15.0), (50.0, 25.0), (65.0, 40.0), (80.0, 65.0), (90.0, 100.0)]
PRESET_BALANCED = [(30.0, 20.0), (45.0, 35.0), (60.0, 50.0), (75.0, 75.0), (85.0, 100.0)]
PRESET_AGGRESSIVE = [(30.0, 35.0), (45.0, 55.0), (60.0, 75.0), (75.0, 95.0), (82.0, 100.0)]


class ThermalView(QWidget):
    """Cooling mode switching and interactive fan curve spline editor."""

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.client = DaemonClient.instance()
        self._current_mode = "auto"
        self._setup_ui()
        self.refresh_state()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(18)

        # Header
        header = QVBoxLayout()
        header.setSpacing(4)
        title = QLabel("THERMAL & COOLING ENGINE")
        title.setProperty("class", "view-title")
        subtitle = QLabel("Hardware PWM modulation, HP EC keep-alive loop, and custom piecewise curve interpolation")
        subtitle.setProperty("class", "view-subtitle")
        header.addWidget(title)
        header.addWidget(subtitle)
        main_layout.addLayout(header)

        # ── Mode Selector Pills ──────────────────────────────────────────────
        pills_card = QFrame()
        pills_card.setProperty("class", "cyber-card")
        pills_layout = QHBoxLayout(pills_card)
        pills_layout.setContentsMargins(16, 12, 16, 12)
        pills_layout.setSpacing(12)

        self.btn_auto = QPushButton("AUTO (BIOS EC)")
        self.btn_auto.setCheckable(True)
        self.btn_auto.setProperty("class", "cyber-btn-secondary")
        self.btn_auto.clicked.connect(lambda: self._set_mode("auto"))
        pills_layout.addWidget(self.btn_auto)

        self.btn_max = QPushButton("MAX TURBO (100% RPM)")
        self.btn_max.setCheckable(True)
        self.btn_max.setProperty("class", "cyber-btn-secondary")
        self.btn_max.clicked.connect(lambda: self._set_mode("max"))
        pills_layout.addWidget(self.btn_max)

        self.btn_custom = QPushButton("CUSTOM CURVE")
        self.btn_custom.setCheckable(True)
        self.btn_custom.setProperty("class", "cyber-btn-secondary")
        self.btn_custom.clicked.connect(lambda: self._set_mode("custom"))
        pills_layout.addWidget(self.btn_custom)

        main_layout.addWidget(pills_card)

        # ── Embedded FanCurveEditor Canvas ───────────────────────────────────
        editor_card = QFrame()
        editor_card.setProperty("class", "cyber-card")
        ed_layout = QVBoxLayout(editor_card)
        ed_layout.setContentsMargins(18, 16, 18, 16)
        ed_layout.setSpacing(12)

        ed_head = QHBoxLayout()
        ed_lbl = QLabel("PIECEWISE LINEAR FAN CURVE")
        ed_lbl.setProperty("class", "card-heading")
        ed_head.addWidget(ed_lbl)
        ed_head.addStretch()

        ed_sub = QLabel("Drag nodes horizontally and vertically (monotonic constraints enforced)")
        ed_sub.setStyleSheet("color: #8E92A4; font-size: 10px;")
        ed_head.addWidget(ed_sub)
        ed_layout.addLayout(ed_head)

        self.curve_editor = FanCurveEditor()
        ed_layout.addWidget(self.curve_editor)

        # Presets & Apply Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        p_lbl = QLabel("PRESETS:")
        p_lbl.setStyleSheet("color: #8E92A4; font-weight: 700; font-size: 10px;")
        toolbar.addWidget(p_lbl)

        btn_silent = QPushButton("Silent")
        btn_silent.setProperty("class", "cyber-btn-secondary")
        btn_silent.clicked.connect(lambda: self.curve_editor.set_curve(PRESET_SILENT))
        toolbar.addWidget(btn_silent)

        btn_bal = QPushButton("Balanced")
        btn_bal.setProperty("class", "cyber-btn-secondary")
        btn_bal.clicked.connect(lambda: self.curve_editor.set_curve(PRESET_BALANCED))
        toolbar.addWidget(btn_bal)

        btn_aggr = QPushButton("Aggressive Gaming")
        btn_aggr.setProperty("class", "cyber-btn-secondary")
        btn_aggr.clicked.connect(lambda: self.curve_editor.set_curve(PRESET_AGGRESSIVE))
        toolbar.addWidget(btn_aggr)

        toolbar.addStretch()

        self.apply_curve_btn = QPushButton("APPLY CURVE")
        self.apply_curve_btn.setProperty("class", "cyber-btn-primary")
        self.apply_curve_btn.clicked.connect(self._apply_curve)
        toolbar.addWidget(self.apply_curve_btn)

        ed_layout.addLayout(toolbar)
        main_layout.addWidget(editor_card)
        main_layout.addStretch()

    def refresh_state(self):
        mode = self.client.get_fan_mode()
        self._update_mode_pills(mode)
        curve = self.client.get_custom_fan_curve()
        if curve:
            self.curve_editor.set_curve(curve)

    def _update_mode_pills(self, mode: str):
        self._current_mode = mode
        self.btn_auto.setChecked(mode == "auto")
        self.btn_max.setChecked(mode == "max")
        self.btn_custom.setChecked(mode == "custom")

        # Styling updates
        for btn, active in [
            (self.btn_auto, mode == "auto"),
            (self.btn_max, mode == "max"),
            (self.btn_custom, mode == "custom"),
        ]:
            if active:
                btn.setStyleSheet("background-color: #00E5FF; color: #0A0B10; font-weight: 800;")
            else:
                btn.setStyleSheet("")

    def _set_mode(self, mode: str):
        self.client.set_fan_mode(mode)
        self._update_mode_pills(mode)

    def _apply_curve(self):
        pts = self.curve_editor.get_curve()
        self.client.set_custom_fan_curve(pts)
        if self._current_mode != "custom":
            self._set_mode("custom")
        QMessageBox.information(self, "Curve Applied", f"Custom fan curve with {len(pts)} nodes sent to root daemon.")

    def update_telemetry(self, m: dict):
        temp = m.get("cpu_temp", 45.0)
        self.curve_editor.set_current_temperature(temp)
