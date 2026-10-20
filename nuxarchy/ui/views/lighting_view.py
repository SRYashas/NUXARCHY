"""
NUXARCHY OMEN Light Studio View
Top: ZoneKeyboardWidget showing live zone colors + [ SELECT ALL ZONES ] button.
Bottom-left: Effect selector (Static, Breathing, Color Cycle, Wave, Off), Brightness slider, and Speed slider.
Bottom-right: Quick Neon Preset Swatches (OMEN Red, Cyber Cyan, Matrix Green, Synthwave Purple, Pure White)
+ QColorDialog custom hex picker and [ APPLY LIGHTING ] button.
"""

from typing import List
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QComboBox,
    QSlider,
    QPushButton,
    QColorDialog,
    QMessageBox,
)
from PyQt6.QtGui import QColor
from nuxarchy.ui.widgets.zone_keyboard import ZoneKeyboardWidget
from nuxarchy.services.daemon_client import DaemonClient

SWATCHES = [
    ("OMEN Red", "#FF0552"),
    ("Cyber Cyan", "#00E5FF"),
    ("Matrix Green", "#00FF66"),
    ("Synthwave Purple", "#9D00FF"),
    ("Pure White", "#FFFFFF"),
]


class LightingView(QWidget):
    """OMEN Light Studio RGB keyboard zone manager and animation effects."""

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.client = DaemonClient.instance()
        self._zone_colors: List[str] = ["#00E5FF", "#00E5FF", "#FF0552", "#FF0552"]
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(18)

        # Header
        header = QVBoxLayout()
        header.setSpacing(4)
        title = QLabel("OMEN LIGHT STUDIO")
        title.setProperty("class", "view-title")
        subtitle = QLabel("Direct HP WMI sysfs multicolor LEDs and OpenRGB SDK raw TCP synchronization")
        subtitle.setProperty("class", "view-subtitle")
        header.addWidget(title)
        header.addWidget(subtitle)
        main_layout.addLayout(header)

        # ── Top Section: ZoneKeyboardWidget + Select All ─────────────────────
        kb_card = QFrame()
        kb_card.setProperty("class", "cyber-card")
        kb_layout = QVBoxLayout(kb_card)
        kb_layout.setContentsMargins(18, 14, 18, 14)
        kb_layout.setSpacing(10)

        kb_head = QHBoxLayout()
        kb_title = QLabel("4-ZONE KEYBOARD CANVAS")
        kb_title.setProperty("class", "card-heading")
        kb_head.addWidget(kb_title)
        kb_head.addStretch()

        self.btn_select_all = QPushButton("SELECT ALL ZONES")
        self.btn_select_all.setProperty("class", "cyber-btn-secondary")
        self.btn_select_all.clicked.connect(self._select_all_zones)
        kb_head.addWidget(self.btn_select_all)
        kb_layout.addLayout(kb_head)

        self.keyboard_widget = ZoneKeyboardWidget()
        self.keyboard_widget.set_all_colors(self._zone_colors)
        kb_layout.addWidget(self.keyboard_widget)

        main_layout.addWidget(kb_card)

        # ── Bottom Split Controls ────────────────────────────────────────────
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(18)

        # Bottom-Left: Effects & Sliders
        left_card = QFrame()
        left_card.setProperty("class", "cyber-card")
        l_layout = QVBoxLayout(left_card)
        l_layout.setContentsMargins(18, 16, 18, 16)
        l_layout.setSpacing(12)

        l_title = QLabel("ANIMATION & INTENSITY")
        l_title.setProperty("class", "card-heading")
        l_layout.addWidget(l_title)

        # Effect Selector
        eff_box = QHBoxLayout()
        eff_lbl = QLabel("LIGHTING EFFECT:")
        eff_lbl.setStyleSheet("color: #FFFFFF; font-weight: 600;")
        self.effect_combo = QComboBox()
        self.effect_combo.addItems(["Static", "Breathing", "Color Cycle", "Wave", "Off"])
        self.effect_combo.setStyleSheet(
            "QComboBox { background-color: #1C1F2E; border: 1px solid #2B3045; "
            "color: #FFFFFF; padding: 6px 12px; border-radius: 4px; font-weight: 700; }"
        )
        eff_box.addWidget(eff_lbl)
        eff_box.addWidget(self.effect_combo)
        l_layout.addLayout(eff_box)

        # Brightness Slider (0-100%)
        b_box = QHBoxLayout()
        b_lbl = QLabel("BRIGHTNESS:")
        b_lbl.setStyleSheet("color: #FFFFFF; font-weight: 600;")
        self.bright_slider = QSlider(Qt.Orientation.Horizontal)
        self.bright_slider.setRange(0, 100)
        self.bright_slider.setValue(100)
        self.bright_val_lbl = QLabel("100%")
        self.bright_val_lbl.setFixedWidth(45)
        self.bright_val_lbl.setStyleSheet("color: #00E5FF; font-weight: 700;")
        self.bright_slider.valueChanged.connect(lambda v: self.bright_val_lbl.setText(f"{v}%"))

        b_box.addWidget(b_lbl)
        b_box.addWidget(self.bright_slider)
        b_box.addWidget(self.bright_val_lbl)
        l_layout.addLayout(b_box)

        # Speed Slider (1-100%)
        s_box = QHBoxLayout()
        s_lbl = QLabel("ANIMATION SPEED:")
        s_lbl.setStyleSheet("color: #FFFFFF; font-weight: 600;")
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(1, 100)
        self.speed_slider.setValue(50)
        self.speed_val_lbl = QLabel("50%")
        self.speed_val_lbl.setFixedWidth(45)
        self.speed_val_lbl.setStyleSheet("color: #00E5FF; font-weight: 700;")
        self.speed_slider.valueChanged.connect(lambda v: self.speed_val_lbl.setText(f"{v}%"))

        s_box.addWidget(s_lbl)
        s_box.addWidget(self.speed_slider)
        s_box.addWidget(self.speed_val_lbl)
        l_layout.addLayout(s_box)

        bottom_layout.addWidget(left_card)

        # Bottom-Right: Swatches & Color Picker
        right_card = QFrame()
        right_card.setProperty("class", "cyber-card")
        r_layout = QVBoxLayout(right_card)
        r_layout.setContentsMargins(18, 16, 18, 16)
        r_layout.setSpacing(12)

        r_title = QLabel("NEON PRESET SWATCHES")
        r_title.setProperty("class", "card-heading")
        r_layout.addWidget(r_title)

        # Swatches Row
        swatch_layout = QHBoxLayout()
        swatch_layout.setSpacing(10)
        for name, hex_code in SWATCHES:
            btn = QPushButton()
            btn.setFixedSize(36, 36)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(
                f"background-color: {hex_code}; border-radius: 6px; border: 2px solid #222533; "
                f"QPushButton:hover {{ border: 2px solid #FFFFFF; }}"
            )
            btn.setToolTip(name)
            btn.clicked.connect(lambda checked, col=hex_code: self._apply_color_to_selected(col))
            swatch_layout.addWidget(btn)
        swatch_layout.addStretch()
        r_layout.addLayout(swatch_layout)

        # Custom Hex & Apply Button
        act_box = QHBoxLayout()
        self.btn_picker = QPushButton("CUSTOM COLOR PICKER")
        self.btn_picker.setProperty("class", "cyber-btn-secondary")
        self.btn_picker.clicked.connect(self._open_color_picker)
        act_box.addWidget(self.btn_picker)

        act_box.addStretch()

        self.btn_apply = QPushButton("APPLY LIGHTING")
        self.btn_apply.setProperty("class", "cyber-btn-primary")
        self.btn_apply.clicked.connect(self._apply_lighting)
        act_box.addWidget(self.btn_apply)
        r_layout.addLayout(act_box)

        bottom_layout.addWidget(right_card)
        main_layout.addLayout(bottom_layout)
        main_layout.addStretch()

    def _select_all_zones(self):
        self.keyboard_widget.set_selected_zone(-1)

    def _apply_color_to_selected(self, hex_color: str):
        sel = self.keyboard_widget.get_selected_zone()
        if sel == -1:
            self._zone_colors = [hex_color] * 4
        elif 0 <= sel < 4:
            self._zone_colors[sel] = hex_color
        self.keyboard_widget.set_zone_color(sel, hex_color)

    def _open_color_picker(self):
        col = QColorDialog.getColor(QColor(self._zone_colors[0]), self, "Pick OMEN Zone Color")
        if col.isValid():
            hex_code = col.name().upper()
            self._apply_color_to_selected(hex_code)

    def _apply_lighting(self):
        mode = self.effect_combo.currentText().lower().replace(" ", "_")
        brightness = self.bright_slider.value()
        speed = self.speed_slider.value()

        ok = self.client.set_lighting(mode, self._zone_colors, brightness, speed)
        if ok:
            QMessageBox.information(
                self,
                "Lighting Applied",
                f"Applied {mode.upper()} effect at {brightness}% brightness across 4 keyboard zones.",
            )
        else:
            QMessageBox.warning(self, "Lighting Warning", "Could not apply lighting via daemon.")
