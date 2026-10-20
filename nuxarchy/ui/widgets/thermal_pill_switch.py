"""
NUXARCHY 3-Way Thermal Pill Switch Widget
Pixel-perfect HP OMEN replica: Pill toggle switch for MAX | AUTO | MANUAL fan control.
Features:
- Pill track: linear horizontal gradient from Blue (#4A90E2) -> Cyan (#4DD0E1) -> Mint/Teal (#64FFDA).
- Inside the track sit 3 stops (left: MAX, center: AUTO, right: MANUAL).
- Active position: crisp white circle (24x24px) containing a fan/snowflake vector icon.
- Three aligned labels underneath: MAX, AUTO, MANUAL (11px uppercase; active is #FFFFFF bold, inactive is #666666).
"""

from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QLinearGradient, QPainterPath
from PyQt6.QtWidgets import QWidget


class ThermalPillSwitch(QWidget):
    """3-Way Pill Switch for Thermal Control (MAX | AUTO | MANUAL)."""

    # Emits "max", "auto", or "manual"
    modeChanged = pyqtSignal(str)

    MODES = ["max", "auto", "manual"]
    LABELS = ["MAX", "AUTO", "MANUAL"]

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setFixedSize(140, 56)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)

        self._active_index = 0  # 0: MAX, 1: AUTO, 2: MANUAL
        self._hover_index = -1

    def current_mode(self) -> str:
        return self.MODES[self._active_index]

    def set_mode(self, mode: str):
        mode_lower = mode.lower()
        if mode_lower in self.MODES:
            idx = self.MODES.index(mode_lower)
            if idx != self._active_index:
                self._active_index = idx
                self.update()
                self.modeChanged.emit(self.MODES[self._active_index])

    def set_mode_silent(self, mode: str):
        """Set mode without emitting modeChanged."""
        mode_lower = mode.lower()
        if mode_lower in self.MODES:
            idx = self.MODES.index(mode_lower)
            if idx != self._active_index:
                self._active_index = idx
                self.update()

    # ── Geometry Calculations ────────────────────────────────────────────────

    def _track_rect(self) -> QRectF:
        track_w = 126.0
        track_h = 30.0
        x = (self.width() - track_w) / 2.0
        y = 2.0
        return QRectF(x, y, track_w, track_h)

    def _stop_centers(self) -> list[QPointF]:
        tr = self._track_rect()
        margin = 17.0
        left_x = tr.left() + margin
        right_x = tr.right() - margin
        center_x = tr.center().x()
        cy = tr.center().y()
        return [QPointF(left_x, cy), QPointF(center_x, cy), QPointF(right_x, cy)]

    # ── Paint Event ──────────────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        tr = self._track_rect()
        radius = tr.height() / 2.0

        # 1. Pill Track Background with 3-stop Horizontal Gradient
        grad = QLinearGradient(tr.topLeft(), tr.topRight())
        grad.setColorAt(0.0, QColor("#4A90E2"))   # Blue
        grad.setColorAt(0.5, QColor("#4DD0E1"))   # Cyan
        grad.setColorAt(1.0, QColor("#64FFDA"))   # Mint / Teal

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(grad))
        painter.drawRoundedRect(tr, radius, radius)

        # 2. Render Inactive Stops (subtle semi-transparent dark circle)
        stops = self._stop_centers()
        for i, center in enumerate(stops):
            if i != self._active_index:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor(255, 255, 255, 60)))
                painter.drawEllipse(center, 9.0, 9.0)

        # 3. Active Position Thumb (24x24px crisp white circle)
        active_center = stops[self._active_index]
        thumb_radius = 12.0

        # Subtle shadow / glow under thumb
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 45)))
        painter.drawEllipse(active_center + QPointF(0, 1.5), thumb_radius, thumb_radius)

        # White circle
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawEllipse(active_center, thumb_radius, thumb_radius)

        # 4. Icon inside active thumb (Stylized Snowflake / Fan Glyph)
        self._draw_fan_glyph(painter, active_center)

        # 5. Bottom Labels (MAX, AUTO, MANUAL)
        labels_y = tr.bottom() + 18.0
        for i, (center, label) in enumerate(zip(stops, self.LABELS)):
            is_active = (i == self._active_index)
            font = QFont("Inter", 9)
            font.setBold(is_active)
            painter.setFont(font)
            painter.setPen(QColor("#FFFFFF" if is_active else "#666666"))

            rect = QRectF(center.x() - 25.0, tr.bottom() + 4.0, 50.0, 18.0)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, label)

    def _draw_fan_glyph(self, painter: QPainter, center: QPointF):
        """Draw a vector 6-spoke snowflake/fan glyph in cyan (#00B0FF)."""
        painter.save()
        painter.translate(center.x(), center.y())
        pen = QPen(QColor("#0091EA"), 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        # Draw 6 spokes
        for angle in (0, 60, 120):
            painter.save()
            painter.rotate(angle)
            painter.drawLine(0, -6, 0, 6)
            # Little side ticks
            painter.drawLine(0, -4, -2, -5)
            painter.drawLine(0, -4, 2, -5)
            painter.drawLine(0, 4, -2, 5)
            painter.drawLine(0, 4, 2, 5)
            painter.restore()

        # Center dot
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#0091EA")))
        painter.drawEllipse(QPointF(0, 0), 1.5, 1.5)

        painter.restore()

    # ── Mouse Interaction ────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()
            stops = self._stop_centers()
            # Find closest stop
            best_idx = 0
            best_dist = 999999.0
            for i, c in enumerate(stops):
                dist = abs(c.x() - pos.x())
                if dist < best_dist:
                    best_dist = dist
                    best_idx = i

            if best_idx != self._active_index:
                self._active_index = best_idx
                self.update()
                self.modeChanged.emit(self.MODES[self._active_index])
