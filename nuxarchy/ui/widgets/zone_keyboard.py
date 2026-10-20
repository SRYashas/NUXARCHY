"""
NUXARCHY Interactive 4-Zone OMEN Laptop Keyboard Widget
Renders an interactive HP OMEN keyboard canvas with 4 distinct lighting zones
(Zone 1: Left, Zone 2: Center-Left, Zone 3: Center-Right, Zone 4: Numpad/Right)
and a highlighted WASD cluster.
"""

from typing import List, Optional
from PyQt6.QtCore import Qt, QRectF, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PyQt6.QtWidgets import QWidget


class ZoneKeyboardWidget(QWidget):
    """Interactive 4-Zone HP OMEN Keyboard layout."""

    zoneSelected = pyqtSignal(int)  # 0 to 3, or -1 for all

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setMinimumSize(480, 180)
        self.setMouseTracking(True)

        self._selected_zone: int = 0  # 0 to 3, -1 for all
        self._zone_colors: List[str] = ["#00E5FF", "#00E5FF", "#FF0552", "#FF0552"]
        self._hovered_zone: Optional[int] = None

    def set_zone_color(self, zone_idx: int, hex_color: str):
        if zone_idx == -1:
            self._zone_colors = [hex_color] * 4
        elif 0 <= zone_idx < 4:
            self._zone_colors[zone_idx] = hex_color
        self.update()

    def set_all_colors(self, hex_colors: List[str]):
        if len(hex_colors) >= 4:
            self._zone_colors = list(hex_colors[:4])
            self.update()

    def set_selected_zone(self, zone_idx: int):
        self._selected_zone = zone_idx
        self.update()

    def get_selected_zone(self) -> int:
        return self._selected_zone

    def _get_zone_rects(self) -> List[QRectF]:
        w = self.width()
        h = self.height()
        pad_x = 24.0
        pad_y = 16.0
        usable_w = w - 2 * pad_x
        usable_h = h - 2 * pad_y

        gap = 8.0
        zone_w = (usable_w - 3 * gap) / 4.0

        rects = []
        for i in range(4):
            rects.append(QRectF(
                pad_x + i * (zone_w + gap),
                pad_y,
                zone_w,
                usable_h,
            ))
        return rects

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw outer keyboard frame
        w = self.width()
        h = self.height()
        frame_rect = QRectF(12, 8, w - 24, h - 16)
        painter.setBrush(QBrush(QColor("#0E1017")))
        painter.setPen(QPen(QColor("#222533"), 1.5))
        painter.drawRoundedRect(frame_rect, 10, 10)

        zone_rects = self._get_zone_rects()
        zone_names = ["ZONE 1 (LEFT)", "ZONE 2 (CENTER-L)", "ZONE 3 (CENTER-R)", "ZONE 4 (NUMPAD)"]

        for idx, rect in enumerate(zone_rects):
            is_selected = (self._selected_zone == idx) or (self._selected_zone == -1)
            is_hovered = self._hovered_zone == idx

            fill_color = QColor(self._zone_colors[idx])
            fill_color.setAlpha(45 if not is_selected else 85)

            # Zone Card Background
            painter.setBrush(QBrush(fill_color))
            if is_selected:
                painter.setPen(QPen(QColor("#FFFFFF"), 2.0))
            elif is_hovered:
                painter.setPen(QPen(QColor("#00E5FF"), 1.5))
            else:
                painter.setPen(QPen(QColor("#222533"), 1.0))

            painter.drawRoundedRect(rect, 8, 8)

            # Draw representative key matrix grid inside zone
            key_cols = 4 if idx < 3 else 3
            key_rows = 4
            kw = (rect.width() - 16) / key_cols
            kh = (rect.height() - 38) / key_rows

            key_pen = QPen(QColor(self._zone_colors[idx]), 1)
            painter.setBrush(QBrush(QColor("#14161F")))
            for r in range(key_rows):
                for c in range(key_cols):
                    kx = rect.left() + 8 + c * kw
                    ky = rect.top() + 10 + r * kh
                    key_rect = QRectF(kx + 2, ky + 2, kw - 4, kh - 4)

                    # Highlight WASD in Zone 1
                    is_wasd = idx == 0 and ((r == 1 and c in (1, 2)) or (r == 2 and c in (1, 2)))
                    if is_wasd:
                        painter.setPen(QPen(QColor("#00E5FF"), 1.5))
                        painter.setBrush(QBrush(QColor(0, 229, 255, 60)))
                    else:
                        painter.setPen(key_pen)
                        painter.setBrush(QBrush(QColor("#14161F")))

                    painter.drawRoundedRect(key_rect, 3, 3)

            # Label at bottom
            painter.setFont(QFont("Inter", 7, QFont.Weight.Bold))
            painter.setPen(QColor("#FFFFFF" if is_selected else "#8E92A4"))
            label_rect = QRectF(rect.left(), rect.bottom() - 24, rect.width(), 20)
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, zone_names[idx])

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()
            rects = self._get_zone_rects()
            for idx, r in enumerate(rects):
                if r.contains(pos):
                    self._selected_zone = idx
                    self.update()
                    self.zoneSelected.emit(idx)
                    break

    def mouseMoveEvent(self, event):
        pos = event.position()
        rects = self._get_zone_rects()
        prev_hover = self._hovered_zone
        self._hovered_zone = None
        for idx, r in enumerate(rects):
            if r.contains(pos):
                self._hovered_zone = idx
                break
        if prev_hover != self._hovered_zone:
            self.update()
