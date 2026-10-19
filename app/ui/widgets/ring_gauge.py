"""
OMEN Gaming Hub Circular Ring Gauge Widget
Matches the exact radial ring gauge styling in HP OMEN Gaming Hub:
Magenta-purple glowing arc, digital percentage, centered metric title,
and bottom-left neon-green temperature readout.
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout, QWidget
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QLinearGradient, QFont
from PySide6.QtCore import Qt, QRectF


class OmenRingGaugeCard(QFrame):
    """Card containing the iconic OMEN circular ring gauge and thermals."""

    def __init__(
        self,
        card_title: str,
        metric_label: str,
        parent=None
    ):
        super().__init__(parent)
        self.setObjectName("omenRingCard")
        self.setProperty("class", "omenCard")
        self.setMinimumSize(210, 240)

        self.card_title = card_title
        self.metric_label = metric_label
        self.current_value = 0.0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        # 1. Card Header Title (e.g. "GPU", "CPU", "RAM")
        self.lbl_card_title = QLabel(card_title.upper())
        self.lbl_card_title.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: 800; letter-spacing: 0.5px;")
        layout.addWidget(self.lbl_card_title)

        # 2. Central Ring Arc Canvas
        self.canvas = _OmenArcCanvas(self)
        layout.addWidget(self.canvas, 1)

        # 3. Bottom Thermals / Memory Details
        self.bottom_layout = QVBoxLayout()
        self.bottom_layout.setSpacing(2)

        self.lbl_temp = QLabel("--")
        self.lbl_temp.setStyleSheet("color: #00FF85; font-size: 18px; font-weight: 800;")
        self.bottom_layout.addWidget(self.lbl_temp)

        self.lbl_temp_sub = QLabel("--")
        self.lbl_temp_sub.setStyleSheet("color: #9CA3AF; font-size: 11px; font-weight: 600;")
        self.bottom_layout.addWidget(self.lbl_temp_sub)

        layout.addLayout(self.bottom_layout)

    def set_data(self, val: float, temp_c: float = None, temp_label: str = "", bottom_detail: str = ""):
        self.current_value = max(0.0, min(100.0, val or 0.0))

        if temp_c is not None:
            self.lbl_temp.setText(f"{temp_c:.0f}°C")
            self.lbl_temp.setStyleSheet("color: #00FF85; font-size: 18px; font-weight: 800;")
            self.lbl_temp_sub.setText(temp_label)
        elif bottom_detail:
            self.lbl_temp.setText(bottom_detail)
            self.lbl_temp.setStyleSheet("color: #9CA3AF; font-size: 12px; font-weight: 600;")
            self.lbl_temp_sub.setText("")

        self.canvas.update()


class _OmenArcCanvas(QWidget):
    def __init__(self, parent_card: OmenRingGaugeCard):
        super().__init__(parent_card)
        self.card = parent_card

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        size = min(w, h) - 10
        rect = QRectF((w - size) / 2.0, (h - size) / 2.0, size, size)

        # 360 degree track with open gap at bottom (or 270 sweep from 225 to -270)
        start_angle = 225 * 16
        span_angle = -270 * 16

        stroke_width = 8

        # 1. Background Track
        track_pen = QPen(QColor(32, 36, 48), stroke_width, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(track_pen)
        painter.drawArc(rect, start_angle, span_angle)

        # 2. Glowing Magenta/Purple/Pink Active Arc
        frac = self.card.current_value / 100.0
        active_span = int(span_angle * frac)

        if abs(active_span) > 0:
            grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
            # OMEN neon purple-pink gradient
            grad.setColorAt(0.0, QColor("#E024C3"))
            grad.setColorAt(1.0, QColor("#9333EA"))

            active_pen = QPen(QBrush(grad), stroke_width, Qt.SolidLine, Qt.RoundCap)
            painter.setPen(active_pen)
            painter.drawArc(rect, start_angle, active_span)

        # 3. Center Digital Readout
        center_x = w / 2.0
        center_y = h / 2.0

        painter.setPen(QColor(255, 255, 255))
        font_pct = QFont("Segoe UI", 26, QFont.Bold)
        painter.setFont(font_pct)
        val_str = f"{int(self.card.current_value)}%"
        painter.drawText(QRectF(0, center_y - 22, w, 32), Qt.AlignCenter, val_str)

        # Sub-metric label below percentage
        painter.setPen(QColor(156, 163, 175))
        font_sub = QFont("Segoe UI", 10, QFont.Bold)
        painter.setFont(font_sub)
        painter.drawText(QRectF(0, center_y + 12, w, 20), Qt.AlignCenter, self.card.metric_label)
