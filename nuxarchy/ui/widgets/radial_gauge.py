"""
NUXARCHY Custom Radial Gauge Widget
Renders an anti-aliased 240-degree circular arc gauge with dual-arc styling,
QConicalGradient transition (#00E5FF Cyan to #FF0552 Cyber Red), smooth QVariantAnimation,
and center metric readout with subtitle badge.
"""

from PyQt6.QtCore import Qt, QRectF, QVariantAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QConicalGradient, QBrush
from PyQt6.QtWidgets import QWidget


class RadialGauge(QWidget):
    """Production-grade cyber-styled circular gauge for telemetry metrics."""

    def __init__(
        self,
        title: str = "CPU TEMP",
        unit: str = "°C",
        min_val: float = 0.0,
        max_val: float = 100.0,
        parent: QWidget = None,
    ):
        super().__init__(parent)
        self.title = title
        self.unit = unit
        self.min_val = min_val
        self.max_val = max_val

        self._value: float = min_val
        self._animated_value: float = min_val
        self._subtitle: str = "--"

        # Smooth value animation (250ms ease-out)
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(250)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.valueChanged.connect(self._on_anim_value_changed)

        self.setMinimumSize(180, 180)

    def _get_animated_val(self) -> float:
        return self._animated_value

    def _set_animated_val(self, val: float):
        self._animated_value = float(val)
        self.update()

    animatedValue = pyqtProperty(float, _get_animated_val, _set_animated_val)

    def _on_anim_value_changed(self, val):
        self._animated_value = float(val)
        self.update()

    def set_value(self, val: float, subtitle: str = ""):
        target = max(self.min_val, min(self.max_val, float(val)))
        self._value = target
        if subtitle:
            self._subtitle = subtitle

        # Start animation from current to target
        self._anim.stop()
        self._anim.setStartValue(self._animated_value)
        self._anim.setEndValue(target)
        self._anim.start()

    def set_subtitle(self, subtitle: str):
        self._subtitle = subtitle
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        side = min(w, h)
        thickness = 12.0
        padding = 16.0

        # Center rect
        rect = QRectF(
            (w - side) / 2.0 + padding,
            (h - side) / 2.0 + padding,
            side - 2 * padding,
            side - 2 * padding,
        )

        center_x = rect.center().x()
        center_y = rect.center().y()

        # 240-degree arc: start angle 210°, span -240°
        # In Qt, 0° is 3 o'clock, angles are in 1/16th of a degree, counter-clockwise positive
        start_angle_deg = 210.0
        span_angle_deg = -240.0

        # 1. Background Track (#222533, thickness 12px, rounded cap)
        bg_pen = QPen(QColor("#222533"), thickness)
        bg_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(bg_pen)
        painter.drawArc(rect, int(start_angle_deg * 16), int(span_angle_deg * 16))

        # 2. Dynamic Foreground Arc
        val_range = self.max_val - self.min_val
        val_pct = (self._animated_value - self.min_val) / (val_range if val_range > 0 else 1.0)
        val_pct = max(0.0, min(1.0, val_pct))

        dynamic_span = span_angle_deg * val_pct

        if abs(dynamic_span) > 0.5:
            # Color transition: #00E5FF (Cyan) -> #FF0552 (Cyber Red/Magenta) above 80%
            if val_pct < 0.8:
                # Interpolate cyan to orange/amber
                fg_color = QColor("#00E5FF")
            else:
                # High alert cyber red
                ratio = (val_pct - 0.8) / 0.2
                r = int(0 + ratio * 255)
                g = int(229 * (1.0 - ratio))
                b = int(255 * (1.0 - ratio * 0.68))
                fg_color = QColor(max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))

            fg_pen = QPen(fg_color, thickness)
            fg_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(fg_pen)
            painter.drawArc(rect, int(start_angle_deg * 16), int(dynamic_span * 16))

        # 3. Center Metric Readout: Title, Large Bold Value, Unit, Subtitle Pill
        painter.setPen(QColor("#8E92A4"))
        title_font = QFont("Inter", 8, QFont.Weight.Bold)
        title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.2)
        painter.setFont(title_font)
        painter.drawText(
            QRectF(center_x - 70, center_y - 45, 140, 20),
            Qt.AlignmentFlag.AlignCenter,
            self.title.upper(),
        )

        # Value readout (28pt, bold, #FFFFFF)
        val_font = QFont("Inter", 26, QFont.Weight.Bold)
        painter.setFont(val_font)
        painter.setPen(QColor("#FFFFFF"))
        val_str = f"{int(round(self._animated_value))}"
        painter.drawText(
            QRectF(center_x - 60, center_y - 20, 90, 36),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            val_str,
        )

        # Unit (11pt, #8E92A4)
        unit_font = QFont("Inter", 11, QFont.Weight.Medium)
        painter.setFont(unit_font)
        painter.setPen(QColor("#8E92A4"))
        painter.drawText(
            QRectF(center_x + 32, center_y - 12, 40, 24),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            self.unit,
        )

        # Subtitle Pill at bottom (e.g. "4.6 GHz" or "65% LOAD")
        if self._subtitle:
            pill_font = QFont("Inter", 8, QFont.Weight.Bold)
            painter.setFont(pill_font)
            pill_rect = QRectF(center_x - 45, center_y + 22, 90, 18)
            painter.setBrush(QBrush(QColor("#1C1F2E")))
            painter.setPen(QPen(QColor("#2B3045"), 1))
            painter.drawRoundedRect(pill_rect, 9, 9)

            painter.setPen(QColor("#00E5FF"))
            painter.drawText(pill_rect, Qt.AlignmentFlag.AlignCenter, self._subtitle)
