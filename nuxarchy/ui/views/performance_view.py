"""
NUXARCHY Performance Control View
Pixel-perfect 1:1 visual and functional replica of the HP OMEN Gaming Hub "Performance Control" tab.
Divided into 3 stacked horizontal sections separated by subtle 1px horizontal dividers (#262626):
1. Top Section: Power Mode
   - Header Bar with "Power Mode" (15px, #FFFFFF, bold), circular (i) info popup,
     "Auto Power Mode Settings" combo, and "Optimized with OMEN Dynamic Power" rotated diamond badge.
   - 3 Centered Mode Cards (ECO, Balanced, Performance) (170x95px) with custom vector icons
     and active gradient border (#FF0055 -> #FF9900).
2. Middle Section: Thermal Control
   - Header Bar with "Thermal Control" (15px, #FFFFFF) + circular (i) info icon.
   - Centered 3-Way Pill Switch (ThermalPillSwitch: MAX | AUTO | MANUAL).
   - QStackedWidget below pill switch:
     * State A (MAX or AUTO): Large centered <RPM> RPM wide sci-fi text + "Fan Speed".
     * State B (MANUAL): 2-Column layout:
       - Left Column: "System fan (<RPM> RPM)", custom slider LOW <-> HIGH,
         and "[ ] Dynamic fan curve" checkbox.
       - Right Column: "CPU: <TEMP>°C" header + 2D FanCurveEditor (50°C-90°C, 9 nodes).
3. Bottom Section: System Temperature
   - Dark panel (#070707, 130px) with "System Temperature" header.
   - 3 Telemetry Columns: CPU Temperature (36px, #00E676), GPU Temperature (36px, #00E676),
     and CPU Utilization (36px, #FFFFFF).
"""

from typing import Dict, Any, Optional
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import (
    QPainter,
    QColor,
    QPen,
    QBrush,
    QFont,
    QLinearGradient,
    QPainterPath,
    QPolygonF,
)
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QComboBox,
    QSlider,
    QCheckBox,
    QStackedWidget,
    QToolTip,
)

from nuxarchy.ui.widgets.thermal_pill_switch import ThermalPillSwitch
from nuxarchy.ui.widgets.fan_curve_editor import FanCurveEditor
from nuxarchy.services.daemon_client import DaemonClient


# ── Custom Info Icon (i) with Styled Popup ───────────────────────────────────

class InfoIconWidget(QWidget):
    """Circular grey (i) info icon (18x18px) that triggers an exact styled tooltip."""

    def __init__(self, tooltip_text: str, parent: QWidget = None):
        super().__init__(parent)
        self.setFixedSize(18, 18)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._tooltip_text = tooltip_text
        self.setToolTip("")  # Use custom handling for precise styling

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(0.5, 0.5, 17.0, 17.0)
        # Circular grey background (#9E9E9E)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#9E9E9E")))
        painter.drawEllipse(rect)

        # Black "i" text
        painter.setPen(QColor("#000000"))
        font = QFont("Georgia", 10, QFont.Weight.Bold)
        font.setItalic(True)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "i")

    def enterEvent(self, event):
        self._show_popup()

    def mousePressEvent(self, event):
        self._show_popup()

    def _show_popup(self):
        # Format HTML styled box (background: #E6E6E6, color: #111111, padding: 12px, border-radius: 4px)
        html = (
            f"<div style='background-color: #E6E6E6; color: #111111; "
            f"border-radius: 4px; padding: 10px; font-family: Inter, sans-serif; "
            f"font-size: 11px; line-height: 1.4; width: 280px;'>"
            f"{self._tooltip_text.replace(chr(10), '<br>')}"
            f"</div>"
        )
        pos = self.mapToGlobal(QPointF(0, self.height() + 4).toPoint())
        QToolTip.showText(pos, html, self)


# ── Rotated Diamond Badge ("OMEN Dynamic Power") ─────────────────────────────

class DynamicPowerBadge(QWidget):
    """Small label + rotated diamond outline badge reading 'OMEN Dynamic Power'."""

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setFixedSize(90, 60)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # "Optimized with" small label
        painter.setFont(QFont("Inter", 8))
        painter.setPen(QColor("#888888"))
        painter.drawText(QRectF(0, 0, self.width(), 14), Qt.AlignmentFlag.AlignCenter, "Optimized with")

        # Rotated Diamond
        cx = self.width() / 2.0
        cy = 36.0
        r = 18.0

        diamond = QPolygonF([
            QPointF(cx, cy - r),
            QPointF(cx + r, cy),
            QPointF(cx, cy + r),
            QPointF(cx - r, cy),
        ])

        painter.setPen(QPen(QColor("#888888"), 1))
        painter.setBrush(QBrush(QColor("#101010")))
        painter.drawPolygon(diamond)

        # "OMEN" inside diamond
        painter.setPen(QColor("#FFFFFF"))
        font_omen = QFont("Inter", 7, QFont.Weight.Bold)
        painter.setFont(font_omen)
        painter.drawText(QRectF(cx - 16, cy - 10, 32, 10), Qt.AlignmentFlag.AlignCenter, "OMEN")

        # "Dynamic" / "Power"
        font_sub = QFont("Inter", 5)
        painter.setFont(font_sub)
        painter.setPen(QColor("#BBBBBB"))
        painter.drawText(QRectF(cx - 16, cy, 32, 7), Qt.AlignmentFlag.AlignCenter, "DYNAMIC")
        painter.drawText(QRectF(cx - 16, cy + 6, 32, 7), Qt.AlignmentFlag.AlignCenter, "POWER")


# ── Custom Power Mode Card (ECO, Balanced, Performance) ──────────────────────

class PowerModeCard(QWidget):
    """
    170x95px Centered Mode Card.
    - Unselected: bg #1A1A1A, border none, icon/text #777777 (13px).
    - Selected: bg #141414, 2px gradient border (#FF0055 -> #FF9900), icon/text #FFFFFF bold (13px).
    """

    clicked = pyqtSignal(str)

    def __init__(self, mode_id: str, label: str, icon_type: str, parent: QWidget = None):
        super().__init__(parent)
        self.mode_id = mode_id
        self.label = label
        self.icon_type = icon_type
        self._is_active = False

        self.setFixedSize(170, 95)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_active(self, active: bool):
        if self._is_active != active:
            self._is_active = active
            self.update()

    def is_active(self) -> bool:
        return self._is_active

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.mode_id)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(1.0, 1.0, self.width() - 2.0, self.height() - 2.0)
        radius = 2.0

        if self._is_active:
            # Active: Background #141414
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor("#141414")))
            painter.drawRoundedRect(rect, radius, radius)

            # 2px Gradient Border (#FF0055 to #FF9900)
            grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
            grad.setColorAt(0.0, QColor("#FF0055"))  # Magenta / Red
            grad.setColorAt(1.0, QColor("#FF9900"))  # Orange / Amber
            border_pen = QPen(QBrush(grad), 2.0)
            painter.setPen(border_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(rect, radius, radius)

            icon_color = QColor("#FFFFFF")
            text_color = QColor("#FFFFFF")
            font = QFont("Inter", 11, QFont.Weight.Bold)
        else:
            # Unselected: Background #1A1A1A, border none
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor("#1A1A1A")))
            painter.drawRoundedRect(rect, radius, radius)

            icon_color = QColor("#777777")
            text_color = QColor("#777777")
            font = QFont("Inter", 11)

        # Render Icon
        self._draw_vector_icon(painter, icon_color)

        # Render Label
        painter.setFont(font)
        painter.setPen(text_color)
        text_rect = QRectF(0, 56, self.width(), 26)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.label)

    def _draw_vector_icon(self, painter: QPainter, color: QColor):
        cx = self.width() / 2.0
        cy = 34.0
        painter.save()
        painter.translate(cx, cy)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(color))

        if self.icon_type == "eco":
            # Double Leaf Icon
            # Left Leaf
            path1 = QPainterPath()
            path1.moveTo(-8, 8)
            path1.cubicTo(-14, 2, -14, -8, -4, -10)
            path1.cubicTo(-2, -4, -3, 3, -8, 8)
            painter.drawPath(path1)

            # Right Leaf
            path2 = QPainterPath()
            path2.moveTo(-4, 6)
            path2.cubicTo(2, 0, 4, -10, 12, -8)
            path2.cubicTo(12, 1, 6, 8, -4, 6)
            painter.drawPath(path2)

        elif self.icon_type == "balanced":
            # Twin Overlapping Diamonds
            r = 9.0
            # Diamond 1 (Left)
            d1 = QPolygonF([
                QPointF(-7, -r),
                QPointF(-7 + r, 0),
                QPointF(-7, r),
                QPointF(-7 - r, 0),
            ])
            # Diamond 2 (Right)
            d2 = QPolygonF([
                QPointF(7, -r),
                QPointF(7 + r, 0),
                QPointF(7, r),
                QPointF(7 - r, 0),
            ])
            painter.setPen(QPen(color, 1.8))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPolygon(d1)
            painter.drawPolygon(d2)

        elif self.icon_type == "performance":
            # 3-Bar Vertical Equalizer / Bar-chart
            w = 3.5
            # Left bar (medium)
            painter.fillRect(QRectF(-8, -4, w, 14), color)
            # Center bar (tall)
            painter.fillRect(QRectF(-8 + 6.5, -12, w, 22), color)
            # Right bar (short)
            painter.fillRect(QRectF(-8 + 13, 0, w, 10), color)

        painter.restore()


# ── Custom Gradient Manual Fan Slider ────────────────────────────────────────

class ManualFanSlider(QSlider):
    """
    Custom 240px horizontal slider for Manual Fan Speed.
    - Unfilled track: #4A4A4A (height: 8px, border-radius: 4px).
    - Filled track: linear gradient from Purple (#7B4296) to Bright Blue (#0088FF).
    - Handle: crisp white circle (18x18px).
    """

    def __init__(self, parent: QWidget = None):
        super().__init__(Qt.Orientation.Horizontal, parent)
        self.setFixedWidth(240)
        self.setFixedHeight(30)
        self.setRange(30, 100)
        self.setValue(50)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        track_h = 8.0
        track_y = (self.height() - track_h) / 2.0
        handle_r = 9.0
        pad_x = handle_r

        track_w = self.width() - (2 * pad_x)
        val_pct = (self.value() - self.minimum()) / float(self.maximum() - self.minimum())
        fill_w = val_pct * track_w

        # 1. Unfilled Track Background (#4A4A4A)
        track_rect = QRectF(pad_x, track_y, track_w, track_h)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#4A4A4A")))
        painter.drawRoundedRect(track_rect, 4.0, 4.0)

        # 2. Filled Track Gradient (#7B4296 -> #0088FF)
        if fill_w > 0:
            fill_rect = QRectF(pad_x, track_y, fill_w, track_h)
            grad = QLinearGradient(track_rect.topLeft(), track_rect.topRight())
            grad.setColorAt(0.0, QColor("#7B4296"))  # Purple
            grad.setColorAt(1.0, QColor("#0088FF"))  # Bright Blue
            painter.setBrush(QBrush(grad))
            painter.drawRoundedRect(fill_rect, 4.0, 4.0)

        # 3. Handle (Crisp White Circle 18x18px)
        handle_cx = pad_x + fill_w
        handle_cy = self.height() / 2.0

        # Subtle shadow
        painter.setBrush(QBrush(QColor(0, 0, 0, 50)))
        painter.drawEllipse(QPointF(handle_cx, handle_cy + 1.0), handle_r, handle_r)

        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawEllipse(QPointF(handle_cx, handle_cy), handle_r, handle_r)


# ── PERFORMANCE VIEW (MAIN TAB) ──────────────────────────────────────────────

class PerformanceView(QWidget):
    """
    1:1 Visual and Functional Replica of HP OMEN Gaming Hub "Performance Control" Tab.
    Divided into 3 horizontal sections:
    - Top Section: Power Mode
    - Middle Section: Thermal Control
    - Bottom Section: System Temperature
    """

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.client = DaemonClient.instance()

        self._current_power_mode = "balanced"
        self._current_thermal_mode = "auto"
        self._current_fan_rpm = 6200
        self._current_cpu_temp = 50.0

        self._setup_ui()
        self.refresh_state()

    def _setup_ui(self):
        self.setObjectName("performanceView")
        self.setStyleSheet("background-color: #0A0A0A; color: #FFFFFF;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 16, 28, 16)
        main_layout.setSpacing(0)

        # ═════════════════════════════════════════════════════════════════════
        # SECTION 1: POWER MODE (TOP SECTION)
        # ═════════════════════════════════════════════════════════════════════
        sec1_container = QWidget()
        sec1_layout = QVBoxLayout(sec1_container)
        sec1_layout.setContentsMargins(0, 0, 0, 16)
        sec1_layout.setSpacing(16)

        # Header Bar
        header1_layout = QHBoxLayout()
        header1_layout.setContentsMargins(0, 0, 0, 0)
        header1_layout.setSpacing(8)

        lbl_power_mode = QLabel("Power Mode")
        lbl_power_mode.setStyleSheet("font-size: 15px; color: #FFFFFF; font-weight: bold; font-family: Inter, sans-serif;")
        header1_layout.addWidget(lbl_power_mode)

        # Info Icon (i) with exact verbatim tooltip
        power_info_text = (
            "ECO - Limits system performance and power consumption to reduce heat and noise level. "
            "When switching to ECO mode, your screen might flicker briefly.\n\n"
            "Balanced - Suitable for common tasks.\n\n"
            "Performance - Suitable for gaming and content creation. May increase heat and noise levels."
        )
        self.power_info_icon = InfoIconWidget(power_info_text)
        header1_layout.addWidget(self.power_info_icon)

        header1_layout.addStretch()

        # Center-Right: Dark dropdown QComboBox
        self.auto_power_combo = QComboBox()
        self.auto_power_combo.setFixedSize(240, 30)
        self.auto_power_combo.addItem("Auto Power Mode Settings")
        self.auto_power_combo.setStyleSheet("""
            QComboBox {
                background-color: #121212;
                color: #FFFFFF;
                border: 1px solid #444444;
                border-radius: 3px;
                padding-left: 10px;
                font-family: Inter, sans-serif;
                font-size: 12px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 24px;
                border-left: 1px solid #333333;
            }
            QComboBox QAbstractItemView {
                background-color: #181818;
                color: #FFFFFF;
                selection-background-color: #262626;
                border: 1px solid #444444;
            }
        """)
        header1_layout.addWidget(self.auto_power_combo)

        header1_layout.addSpacing(16)

        # Far-Right: Rotated diamond badge
        self.badge_widget = DynamicPowerBadge()
        header1_layout.addWidget(self.badge_widget)

        sec1_layout.addLayout(header1_layout)

        # 3 Centered Mode Cards (ECO, Balanced, Performance)
        cards_row = QHBoxLayout()
        cards_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cards_row.setSpacing(24)

        self.card_eco = PowerModeCard("eco", "ECO", "eco")
        self.card_eco.clicked.connect(self._on_power_mode_clicked)
        cards_row.addWidget(self.card_eco)

        self.card_balanced = PowerModeCard("balanced", "Balanced", "balanced")
        self.card_balanced.clicked.connect(self._on_power_mode_clicked)
        cards_row.addWidget(self.card_balanced)

        self.card_perf = PowerModeCard("performance", "Performance", "performance")
        self.card_perf.clicked.connect(self._on_power_mode_clicked)
        cards_row.addWidget(self.card_perf)

        sec1_layout.addLayout(cards_row)
        main_layout.addWidget(sec1_container)

        # Divider 1 (1px solid #262626)
        div1 = QFrame()
        div1.setFrameShape(QFrame.Shape.HLine)
        div1.setStyleSheet("background-color: #262626; border: none; min-height: 1px; max-height: 1px;")
        main_layout.addWidget(div1)

        # ═════════════════════════════════════════════════════════════════════
        # SECTION 2: THERMAL CONTROL (MIDDLE SECTION)
        # ═════════════════════════════════════════════════════════════════════
        sec2_container = QWidget()
        sec2_layout = QVBoxLayout(sec2_container)
        sec2_layout.setContentsMargins(0, 14, 0, 14)
        sec2_layout.setSpacing(10)

        # Section Header: Bold "Thermal Control" + (i) info icon
        header2_layout = QHBoxLayout()
        header2_layout.setSpacing(8)

        lbl_thermal_control = QLabel("Thermal Control")
        lbl_thermal_control.setStyleSheet("font-size: 15px; color: #FFFFFF; font-weight: bold; font-family: Inter, sans-serif;")
        header2_layout.addWidget(lbl_thermal_control)

        thermal_info_text = "Optimizes overall cooling by selecting between Max, Auto, and Manual fan speed control."
        self.thermal_info_icon = InfoIconWidget(thermal_info_text)
        header2_layout.addWidget(self.thermal_info_icon)
        header2_layout.addStretch()

        sec2_layout.addLayout(header2_layout)

        # Centered 3-Position Pill Toggle (ThermalPillSwitch)
        pill_row = QHBoxLayout()
        pill_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pill_switch = ThermalPillSwitch()
        self.pill_switch.modeChanged.connect(self._on_thermal_mode_changed)
        pill_row.addWidget(self.pill_switch)

        sec2_layout.addLayout(pill_row)

        # QStackedWidget below pill switch for Dynamic Sub-Views
        self.thermal_stack = QStackedWidget()

        # ─────────────────────────────────────────────────────────────────────
        # State A: When MAX or AUTO is selected
        # ─────────────────────────────────────────────────────────────────────
        self.state_a_widget = QWidget()
        state_a_layout = QVBoxLayout(self.state_a_widget)
        state_a_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        state_a_layout.setContentsMargins(0, 20, 0, 20)
        state_a_layout.setSpacing(4)

        # Line 1: <RPM> RPM in futuristic wide display font
        self.lbl_rpm_state_a = QLabel("6200 RPM")
        self.lbl_rpm_state_a.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_rpm_state_a.setStyleSheet("""
            color: #FFFFFF;
            font-size: 22px;
            font-weight: bold;
            font-family: Orbitron, Eurostile, "Segoe UI", sans-serif;
            letter-spacing: 1.5px;
        """)
        state_a_layout.addWidget(self.lbl_rpm_state_a)

        # Line 2: "Fan Speed" (12px, #888888)
        lbl_fan_speed_sub = QLabel("Fan Speed")
        lbl_fan_speed_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_fan_speed_sub.setStyleSheet("color: #888888; font-size: 12px; font-family: Inter, sans-serif;")
        state_a_layout.addWidget(lbl_fan_speed_sub)

        self.thermal_stack.addWidget(self.state_a_widget)  # Index 0: MAX / AUTO

        # ─────────────────────────────────────────────────────────────────────
        # State B: When MANUAL is selected (2-Column Layout)
        # ─────────────────────────────────────────────────────────────────────
        self.state_b_widget = QWidget()
        state_b_layout = QHBoxLayout(self.state_b_widget)
        state_b_layout.setContentsMargins(10, 10, 10, 10)
        state_b_layout.setSpacing(40)
        state_b_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Left Column: Static / Knob Slider Control
        left_col = QVBoxLayout()
        left_col.setSpacing(8)
        left_col.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Top Label: "System fan (6300 RPM)" + (i) icon
        lbl_sys_fan_row = QHBoxLayout()
        lbl_sys_fan_row.setSpacing(6)
        self.lbl_system_fan = QLabel("System fan  (6200 RPM)")
        self.lbl_system_fan.setStyleSheet("font-size: 14px; color: #FFFFFF; font-weight: bold; font-family: Inter, sans-serif;")
        lbl_sys_fan_row.addWidget(self.lbl_system_fan)

        fan_slider_info = "Adjust static fan RPM slider or toggle dynamic temperature curve."
        lbl_sys_fan_row.addWidget(InfoIconWidget(fan_slider_info))
        lbl_sys_fan_row.addStretch()
        left_col.addLayout(lbl_sys_fan_row)

        left_col.addSpacing(6)

        # Custom Horizontal Slider (LOW <-> HIGH)
        self.fan_slider = ManualFanSlider()
        self.fan_slider.valueChanged.connect(self._on_slider_value_changed)
        left_col.addWidget(self.fan_slider)

        # Labels directly under slider ends: "LOW" (#777777) and "HIGH" (#FFFFFF bold)
        slider_labels_row = QHBoxLayout()
        slider_labels_row.setContentsMargins(0, 0, 0, 0)
        lbl_low = QLabel("LOW")
        lbl_low.setStyleSheet("color: #777777; font-size: 11px; font-weight: bold; font-family: Inter, sans-serif;")
        slider_labels_row.addWidget(lbl_low)

        slider_labels_row.addStretch()

        lbl_high = QLabel("HIGH")
        lbl_high.setStyleSheet("color: #FFFFFF; font-size: 11px; font-weight: bold; font-family: Inter, sans-serif;")
        slider_labels_row.addWidget(lbl_high)

        # Keep labels width aligned with slider width
        slider_labels_container = QWidget()
        slider_labels_container.setFixedWidth(240)
        slider_labels_container.setLayout(slider_labels_row)
        left_col.addWidget(slider_labels_container)

        left_col.addSpacing(24)

        # Checkbox [ ] Dynamic fan curve
        self.chk_dynamic_curve = QCheckBox("Dynamic fan curve")
        self.chk_dynamic_curve.setStyleSheet("""
            QCheckBox {
                color: #FFFFFF;
                font-size: 13px;
                font-family: Inter, sans-serif;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                background-color: #111111;
                border: 1px solid #777777;
                border-radius: 2px;
            }
            QCheckBox::indicator:checked {
                background-color: #0088FF;
                border: 1px solid #0088FF;
            }
        """)
        self.chk_dynamic_curve.toggled.connect(self._on_dynamic_curve_toggled)
        left_col.addWidget(self.chk_dynamic_curve)

        state_b_layout.addLayout(left_col)

        # Right Column: 2D Fan Curve Graph
        right_col = QVBoxLayout()
        right_col.setSpacing(6)
        right_col.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Header above graph: "CPU: <TEMP>°C"
        self.lbl_cpu_temp_header = QLabel("CPU: 50°C")
        self.lbl_cpu_temp_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_cpu_temp_header.setStyleSheet("font-size: 13px; color: #FFFFFF; font-weight: bold; font-family: Inter, sans-serif;")
        right_col.addWidget(self.lbl_cpu_temp_header)

        # 2D Graph Canvas (FanCurveEditor)
        self.fan_curve_editor = FanCurveEditor()
        self.fan_curve_editor.curveChanged.connect(self._on_curve_changed)
        right_col.addWidget(self.fan_curve_editor)

        state_b_layout.addLayout(right_col)

        self.thermal_stack.addWidget(self.state_b_widget)  # Index 1: MANUAL

        sec2_layout.addWidget(self.thermal_stack)
        main_layout.addWidget(sec2_container)

        # Divider 2 (1px solid #262626)
        div2 = QFrame()
        div2.setFrameShape(QFrame.Shape.HLine)
        div2.setStyleSheet("background-color: #262626; border: none; min-height: 1px; max-height: 1px;")
        main_layout.addWidget(div2)

        # ═════════════════════════════════════════════════════════════════════
        # SECTION 3: SYSTEM TEMPERATURE (BOTTOM SECTION)
        # ═════════════════════════════════════════════════════════════════════
        sec3_panel = QFrame()
        sec3_panel.setFixedHeight(120)
        sec3_panel.setStyleSheet("background-color: #070707; border-radius: 4px;")
        sec3_layout = QVBoxLayout(sec3_panel)
        sec3_layout.setContentsMargins(18, 12, 18, 12)
        sec3_layout.setSpacing(6)

        # Header: "System Temperature"
        lbl_sys_temp_title = QLabel("System Temperature")
        lbl_sys_temp_title.setStyleSheet("font-size: 15px; color: #FFFFFF; font-weight: bold; font-family: Inter, sans-serif;")
        sec3_layout.addWidget(lbl_sys_temp_title)

        # Three Telemetry Columns Centered Horizontally
        telem_row = QHBoxLayout()
        telem_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        telem_row.setSpacing(60)

        # Col 1: CPU Temperature
        col1 = QVBoxLayout()
        col1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col1.setSpacing(2)
        self.lbl_cpu_temp_val = QLabel("50°C")
        self.lbl_cpu_temp_val.setStyleSheet("""
            color: #00E676;
            font-size: 34px;
            font-weight: bold;
            font-family: Orbitron, Eurostile, "Segoe UI", sans-serif;
        """)
        self.lbl_cpu_temp_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col1.addWidget(self.lbl_cpu_temp_val)

        lbl_cpu_title = QLabel("CPU Temperature")
        lbl_cpu_title.setStyleSheet("color: #777777; font-size: 12px; font-family: Inter, sans-serif;")
        lbl_cpu_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col1.addWidget(lbl_cpu_title)
        telem_row.addLayout(col1)

        # Col 2: GPU Temperature
        col2 = QVBoxLayout()
        col2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col2.setSpacing(2)
        self.lbl_gpu_temp_val = QLabel("48°C")
        self.lbl_gpu_temp_val.setStyleSheet("""
            color: #00E676;
            font-size: 34px;
            font-weight: bold;
            font-family: Orbitron, Eurostile, "Segoe UI", sans-serif;
        """)
        self.lbl_gpu_temp_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col2.addWidget(self.lbl_gpu_temp_val)

        lbl_gpu_title = QLabel("GPU Temperature")
        lbl_gpu_title.setStyleSheet("color: #777777; font-size: 12px; font-family: Inter, sans-serif;")
        lbl_gpu_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col2.addWidget(lbl_gpu_title)
        telem_row.addLayout(col2)

        # Col 3: CPU Utilization
        col3 = QVBoxLayout()
        col3.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col3.setSpacing(2)
        self.lbl_cpu_util_val = QLabel("15%")
        self.lbl_cpu_util_val.setStyleSheet("""
            color: #FFFFFF;
            font-size: 34px;
            font-weight: bold;
            font-family: Orbitron, Eurostile, "Segoe UI", sans-serif;
        """)
        self.lbl_cpu_util_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col3.addWidget(self.lbl_cpu_util_val)

        lbl_util_title = QLabel("CPU Utilization")
        lbl_util_title.setStyleSheet("color: #777777; font-size: 12px; font-family: Inter, sans-serif;")
        lbl_util_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col3.addWidget(lbl_util_title)
        telem_row.addLayout(col3)

        sec3_layout.addLayout(telem_row)
        main_layout.addWidget(sec3_panel)

    # ── State Refresh & Hardware Synchronization ─────────────────────────────

    def refresh_state(self):
        """Query daemon state and synchronize UI controls."""
        # 1. Platform Profile
        profile = self.client.get_platform_profile()
        self._current_power_mode = profile.lower()
        self.card_eco.set_active("eco" in self._current_power_mode or "low-power" in self._current_power_mode)
        self.card_balanced.set_active("balanced" in self._current_power_mode)
        self.card_perf.set_active("perf" in self._current_power_mode)

        # 2. Thermal Mode
        fan_mode = self.client.get_fan_mode()
        self._current_thermal_mode = fan_mode.lower()
        if self._current_thermal_mode in ("custom", "manual"):
            self.pill_switch.set_mode_silent("manual")
            self.thermal_stack.setCurrentIndex(1)
        elif self._current_thermal_mode == "max":
            self.pill_switch.set_mode_silent("max")
            self.thermal_stack.setCurrentIndex(0)
        else:
            self.pill_switch.set_mode_silent("auto")
            self.thermal_stack.setCurrentIndex(0)

        # 3. Dynamic Curve & Static Slider state
        dynamic_active = self.client.is_dynamic_curve_enabled()
        self.chk_dynamic_curve.blockSignals(True)
        self.chk_dynamic_curve.setChecked(dynamic_active)
        self.chk_dynamic_curve.blockSignals(False)

        manual_speed = self.client.get_manual_fan_speed()
        self.fan_slider.blockSignals(True)
        self.fan_slider.setValue(manual_speed)
        self.fan_slider.setEnabled(not dynamic_active)
        self.fan_slider.blockSignals(False)

        # 4. Fan curve points
        curve = self.client.get_custom_fan_curve()
        if curve:
            self.fan_curve_editor.set_curve(curve)

    def update_telemetry(self, metrics: Dict[str, Any]):
        """Called by MainWindow telemetry timer (every 1000ms-1500ms)."""
        cpu_t = metrics.get("cpu_temp_c", 50.0)
        gpu_t = metrics.get("gpu_temp_c", 48.0)
        cpu_u = metrics.get("cpu_usage_pct", 15.0)
        fan_rpm = int(metrics.get("fan1_rpm", 0))
        if fan_rpm <= 0:
            # Fallback estimation based on PWM
            pwm = metrics.get("current_pwm", 65.0)
            fan_rpm = int(1200 + (pwm / 255.0) * 5000)

        self._current_fan_rpm = fan_rpm
        self._current_cpu_temp = cpu_t

        # State A & State B live Fan readouts
        self.lbl_rpm_state_a.setText(f"{fan_rpm} RPM")
        self.lbl_system_fan.setText(f"System fan  ({fan_rpm} RPM)")

        # Right Column Header in Manual Mode
        self.lbl_cpu_temp_header.setText(f"CPU: {int(round(cpu_t))}°C")
        self.fan_curve_editor.set_current_temperature(cpu_t)

        # Bottom Section Telemetry Values
        self.lbl_cpu_temp_val.setText(f"{int(round(cpu_t))}°C")
        self.lbl_gpu_temp_val.setText(f"{int(round(gpu_t))}°C")
        self.lbl_cpu_util_val.setText(f"{int(round(cpu_u))}%")

    # ── UI Handlers ──────────────────────────────────────────────────────────

    def _on_power_mode_clicked(self, mode_id: str):
        """User clicked one of ECO, Balanced, or Performance."""
        self._current_power_mode = mode_id
        self.card_eco.set_active(mode_id == "eco")
        self.card_balanced.set_active(mode_id == "balanced")
        self.card_perf.set_active(mode_id == "performance")
        self.client.set_platform_profile(mode_id)

    def _on_thermal_mode_changed(self, mode_id: str):
        """User toggled MAX, AUTO, or MANUAL on pill switch."""
        self._current_thermal_mode = mode_id
        if mode_id == "manual":
            self.thermal_stack.setCurrentIndex(1)
            self.client.set_fan_mode("manual")
        elif mode_id == "max":
            self.thermal_stack.setCurrentIndex(0)
            self.client.set_fan_mode("max")
        else:
            self.thermal_stack.setCurrentIndex(0)
            self.client.set_fan_mode("auto")

    def _on_slider_value_changed(self, value: int):
        """User dragged manual fan speed slider (LOW <-> HIGH)."""
        self.client.set_manual_fan_speed(value)
        # Update curve editor nodes to reflect static flat level
        self.fan_curve_editor.set_all_nodes_speed(value)

    def _on_dynamic_curve_toggled(self, checked: bool):
        """User toggled [ ] Dynamic fan curve."""
        self.fan_slider.setEnabled(not checked)
        self.client.set_dynamic_curve_enabled(checked)
        if checked:
            # Send current editor curve to daemon
            curve = self.fan_curve_editor.get_curve()
            self.client.set_custom_fan_curve(curve)
        else:
            # Revert to static slider speed
            self.client.set_manual_fan_speed(self.fan_slider.value())

    def _on_curve_changed(self, curve_points: list):
        """User dragged a node on 2D fan curve."""
        self.client.set_custom_fan_curve(curve_points)
