"""
NUXARCHY Light Studio: 4-Zone RGB Keyboard Control View
Features realistic keyboard zone layouts, glowing animated keycaps,
palette swatches, and hardware WMI lighting control.
"""

import time
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QSlider, QComboBox, QColorDialog, QGridLayout, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from nuxarchy.backend.capability import HardwareCapabilities
from nuxarchy.backend.adapters.lighting_adapter import LightingAdapter, LightingProfile, RgbColor


class LightingView(QWidget):
    def __init__(self, caps: HardwareCapabilities, parent=None):
        super().__init__(parent)
        self.caps = caps
        self.adapter = LightingAdapter()
        self.profile = LightingProfile()
        self.start_time = time.time()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(18)

        # Header
        header = QHBoxLayout()
        header_text = QVBoxLayout()
        title = QLabel("NUXARCHY LIGHT STUDIO")
        title.setStyleSheet("color: #FFFFFF; font-size: 22px; font-weight: 800; letter-spacing: 1px;")
        header_text.addWidget(title)

        sub = QLabel("4-Zone RGB Keyboard Lighting & Dynamic Effect Studio")
        sub.setStyleSheet("color: #9CA3AF; font-size: 12px;")
        header_text.addWidget(sub)
        header.addLayout(header_text)
        header.addStretch()
        layout.addLayout(header)

        # Keyboard Chassis Mockup
        kb_chassis = QFrame()
        kb_chassis.setStyleSheet("""
            QFrame {
                background-color: #0E1015;
                border: 2px solid #202430;
                border-radius: 14px;
                padding: 16px;
            }
        """)
        chassis_layout = QVBoxLayout(kb_chassis)
        chassis_layout.setSpacing(12)

        kb_label = QLabel("KEYBOARD MATRIX (4 INDEPENDENT RGB ZONES)")
        kb_label.setStyleSheet("color: #6B7280; font-size: 10px; font-weight: 800; letter-spacing: 1.5px;")
        chassis_layout.addWidget(kb_label)

        # 4 Interactive Zones
        zones_row = QHBoxLayout()
        zones_row.setSpacing(10)

        self.zone_frames = []
        zone_specs = [
            ("ZONE 1", "Left Cluster\n[Esc, Tab, Q, A, Shift]"),
            ("ZONE 2", "WASD Cluster\n[W, A, S, D, Space]"),
            ("ZONE 3", "Center-Right\n[YUIOP, HJKL, Enter]"),
            ("ZONE 4", "Numpad & Arrows\n[Num, Arrows, Del]")
        ]

        for i, (z_title, z_desc) in enumerate(zone_specs):
            z_card = QFrame()
            z_card.setMinimumHeight(140)
            z_card.setCursor(Qt.PointingHandCursor)
            z_layout = QVBoxLayout(z_card)
            z_layout.setAlignment(Qt.AlignCenter)

            lbl_t = QLabel(z_title)
            lbl_t.setAlignment(Qt.AlignCenter)
            lbl_t.setStyleSheet("color: #FFFFFF; font-weight: 800; font-size: 13px;")
            z_layout.addWidget(lbl_t)

            lbl_d = QLabel(z_desc)
            lbl_d.setAlignment(Qt.AlignCenter)
            lbl_d.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 11px;")
            z_layout.addWidget(lbl_d)

            lbl_hex = QLabel(self.profile.zone_colors[i].to_hex())
            lbl_hex.setAlignment(Qt.AlignCenter)
            lbl_hex.setStyleSheet("color: #FFFFFF; font-family: monospace; font-weight: 700; font-size: 12px; margin-top: 6px;")
            z_layout.addWidget(lbl_hex)

            z_card.zone_idx = i
            z_card.lbl_hex = lbl_hex
            z_card.mousePressEvent = lambda e, idx=i: self._pick_color(idx)
            self.zone_frames.append(z_card)
            zones_row.addWidget(z_card)

        chassis_layout.addLayout(zones_row)
        layout.addWidget(kb_chassis)

        # Effect Controls Card
        ctrl_card = QFrame()
        ctrl_card.setProperty("class", "cardFrame")
        c_layout = QVBoxLayout(ctrl_card)
        c_layout.setSpacing(16)

        # Row 1: Mode & Direction
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Effect Animation:"))
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["Wave", "ColorCycle", "Breathing", "Static", "Off"])
        self.combo_mode.currentTextChanged.connect(self._on_mode_changed)
        row1.addWidget(self.combo_mode)

        row1.addSpacing(20)
        row1.addWidget(QLabel("Wave Direction:"))
        self.combo_dir = QComboBox()
        self.combo_dir.addItems(["Right", "Left"])
        self.combo_dir.currentTextChanged.connect(lambda t: setattr(self.profile, "direction", t))
        row1.addWidget(self.combo_dir)

        row1.addStretch()
        c_layout.addLayout(row1)

        # Row 2: Sliders
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Brightness:"))
        self.slider_bright = QSlider(Qt.Horizontal)
        self.slider_bright.setRange(0, 100)
        self.slider_bright.setValue(100)
        self.slider_bright.valueChanged.connect(self._on_brightness_changed)
        row2.addWidget(self.slider_bright)
        self.lbl_bright_val = QLabel("100%")
        self.lbl_bright_val.setStyleSheet("color: #00FFD1; font-weight: 700; width: 40px;")
        row2.addWidget(self.lbl_bright_val)

        row2.addSpacing(20)
        row2.addWidget(QLabel("Animation Speed:"))
        self.slider_speed = QSlider(Qt.Horizontal)
        self.slider_speed.setRange(1, 100)
        self.slider_speed.setValue(50)
        self.slider_speed.valueChanged.connect(lambda v: setattr(self.profile, "speed", v))
        row2.addWidget(self.slider_speed)

        c_layout.addLayout(row2)

        # Row 3: Presets & Apply
        row3 = QHBoxLayout()
        btn_apply = QPushButton("APPLY TO HARDWARE")
        btn_apply.setProperty("class", "primaryButton")
        btn_apply.clicked.connect(self._apply_lighting)
        row3.addWidget(btn_apply)

        btn_cyber_red = QPushButton("Cyber Red Theme")
        btn_cyber_red.setProperty("class", "secondaryButton")
        btn_cyber_red.clicked.connect(lambda: self._set_preset([RgbColor(255, 42, 84)] * 4))
        row3.addWidget(btn_cyber_red)

        btn_cyber = QPushButton("Cyberpunk Turquoise")
        btn_cyber.setProperty("class", "secondaryButton")
        btn_cyber.clicked.connect(lambda: self._set_preset([RgbColor(0, 255, 209), RgbColor(255, 42, 84), RgbColor(157, 78, 221), RgbColor(0, 255, 209)]))
        row3.addWidget(btn_cyber)

        btn_ice = QPushButton("Glacier Blue")
        btn_ice.setProperty("class", "secondaryButton")
        btn_ice.clicked.connect(lambda: self._set_preset([RgbColor(0, 180, 216), RgbColor(144, 224, 239), RgbColor(0, 119, 182), RgbColor(0, 180, 216)]))
        row3.addWidget(btn_ice)

        row3.addStretch()
        c_layout.addLayout(row3)

        layout.addWidget(ctrl_card)
        layout.addStretch()

        # 30 FPS Animation Timer
        self.timer = QTimer(self)
        self.timer.setInterval(33)
        self.timer.timeout.connect(self._animate_preview)
        self.timer.start()

        self._render_zones(self.profile.zone_colors)

    def _pick_color(self, idx: int):
        curr = self.profile.zone_colors[idx]
        color = QColorDialog.getColor(QColor(curr.r, curr.g, curr.b), self, f"Select Color for Zone {idx + 1}")
        if color.isValid():
            self.profile.zone_colors[idx] = RgbColor(color.red(), color.green(), color.blue())
            self.profile.mode = "Static"
            self.combo_mode.setCurrentText("Static")
            self._render_zones(self.profile.zone_colors)

    def _set_preset(self, colors: list):
        self.profile.zone_colors = colors
        self._render_zones(colors)
        self._apply_lighting()

    def _on_mode_changed(self, mode: str):
        self.profile.mode = mode
        self.start_time = time.time()

    def _on_brightness_changed(self, val: int):
        self.profile.brightness = val
        self.lbl_bright_val.setText(f"{val}%")

    def _animate_preview(self):
        elapsed = time.time() - self.start_time
        frame = self.adapter.calculate_animated_frame(self.profile, elapsed)
        self._render_zones(frame)

    def _render_zones(self, colors: list):
        for i, card in enumerate(self.zone_frames):
            c = colors[i]
            hex_c = c.to_hex()
            card.setStyleSheet(f"""
                QFrame {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {hex_c}, stop:1 rgba(15, 17, 23, 0.85));
                    border: 2px solid rgba(255, 255, 255, 0.35);
                    border-radius: 10px;
                }}
            """)
            card.lbl_hex.setText(hex_c)

    def _apply_lighting(self):
        success, msg = self.adapter.apply_profile(self.profile)
        if success:
            QMessageBox.information(self, "NUXARCHY Light Studio", msg)
        else:
            QMessageBox.warning(self, "Lighting Warning", msg)
