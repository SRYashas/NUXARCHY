"""
NUXARCHY Interactive Fan Curve Editor Widget
Pixel-perfect HP OMEN replica:
- 2D Canvas with outer border (1px solid #888888) and dark background (#080808).
- 8x8 dark grid lines (1px solid #1F1F1F).
- Y-Axis Labels: "Max" at top, "RPM" in middle, "Min" at bottom (11px, #888888).
- X-Axis Labels: "50°C" at left corner, "Temperature" in middle, "90°C" at right corner (11px, #888888).
- 9 equidistant temperature nodes spanning horizontally from 50°C to 90°C:
  50°C, 55°C, 60°C, 65°C, 70°C, 75°C, 80°C, 85°C, 90°C.
- Connected by continuous blue polyline (#2563EB, 2.5px), with horizontal lead-in/lead-out lines.
- Each node drawn as glowing circle (radius 4px) with outer blue halo (radius 7px, #3B82F6).
- Draggable vertically with monotonic constraints.
"""

from typing import List, Tuple, Optional
from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPainterPath
from PyQt6.QtWidgets import QWidget


class FanCurveEditor(QWidget):
    """Interactive 2D 9-Node Fan Curve Editor."""

    curveChanged = pyqtSignal(list)

    # 9 Equidistant Temperatures
    TEMP_POINTS = [50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0]

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setFixedSize(330, 240)
        self.setMouseTracking(True)

        self.min_temp = 50.0
        self.max_temp = 90.0
        self.min_speed = 0.0
        self.max_speed = 100.0

        # Default 9 nodes matching reference screenshot 2:
        # starts around 25% at 50°C, ramps up monotonically to ~90% at 90°C
        self._nodes: List[List[float]] = [
            [50.0, 25.0],
            [55.0, 32.0],
            [60.0, 40.0],
            [65.0, 48.0],
            [70.0, 56.0],
            [75.0, 64.0],
            [80.0, 72.0],
            [85.0, 82.0],
            [90.0, 92.0],
        ]

        self._dragged_node_idx: Optional[int] = None
        self._hovered_node_idx: Optional[int] = None
        self._current_temp: float = 50.0

    def set_curve(self, points: List[Tuple[float, float]]):
        """Set curve points."""
        if not points:
            return
        self._nodes = [[float(p[0]), float(p[1])] for p in points]
        self._nodes.sort(key=lambda p: p[0])
        self.update()

    def _interpolate_speed_at(self, temp: float, points: List[Tuple[float, float]]) -> float:
        pts = sorted(points, key=lambda p: p[0])
        if temp <= pts[0][0]:
            return float(pts[0][1])
        if temp >= pts[-1][0]:
            return float(pts[-1][1])
        for i in range(len(pts) - 1):
            t1, s1 = pts[i]
            t2, s2 = pts[i + 1]
            if t1 <= temp <= t2:
                if t2 == t1:
                    return float(s1)
                frac = (temp - t1) / (t2 - t1)
                return float(s1 + frac * (s2 - s1))
        return 50.0

    def get_curve(self) -> List[Tuple[float, float]]:
        return [(p[0], p[1]) for p in self._nodes]

    def set_all_nodes_speed(self, speed_pct: float):
        """Set all nodes to a flat static percentage (used when manual slider drags)."""
        clamped = max(0.0, min(100.0, float(speed_pct)))
        for n in self._nodes:
            n[1] = clamped
        self.update()
        self.curveChanged.emit(self.get_curve())

    def set_current_temperature(self, temp: float):
        self._current_temp = float(temp)
        self.update()

    # ── Geometry & Layout ────────────────────────────────────────────────────

    def _graph_rect(self) -> QRectF:
        pad_left = 40.0
        pad_right = 16.0
        pad_top = 10.0
        pad_bottom = 28.0
        return QRectF(
            pad_left,
            pad_top,
            self.width() - pad_left - pad_right,
            self.height() - pad_top - pad_bottom,
        )

    def _temp_speed_to_pixel(self, temp: float, speed: float) -> QPointF:
        gr = self._graph_rect()
        # Horizontal fraction across 50°C..90°C with small margins for lead-in/lead-out
        # In reference screenshot 2: node 0 (50°C) is slightly offset from left, node 8 (90°C) offset from right
        inner_margin_x = 10.0
        plot_w = gr.width() - (2 * inner_margin_x)
        x_pct = (temp - self.min_temp) / (self.max_temp - self.min_temp)
        px = gr.left() + inner_margin_x + x_pct * plot_w

        y_pct = (speed - self.min_speed) / (self.max_speed - self.min_speed)
        py = gr.bottom() - y_pct * gr.height()
        return QPointF(px, py)

    def _pixel_to_speed(self, py: float) -> float:
        gr = self._graph_rect()
        y_pct = max(0.0, min(1.0, (gr.bottom() - py) / gr.height()))
        return self.min_speed + y_pct * (self.max_speed - self.min_speed)

    # ── Paint Event ──────────────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        gr = self._graph_rect()

        # 1. Outer Canvas Background & Border
        painter.fillRect(gr, QColor("#080808"))
        painter.setPen(QPen(QColor("#888888"), 1))
        painter.drawRect(gr)

        # 2. Internal 8x8 Grid Lines (#1F1F1F)
        grid_pen = QPen(QColor("#1F1F1F"), 1, Qt.PenStyle.SolidLine)
        painter.setPen(grid_pen)

        # 8 grid divisions = 7 interior lines
        for i in range(1, 8):
            # Horizontal lines
            y = gr.top() + i * (gr.height() / 8.0)
            painter.drawLine(QPointF(gr.left(), y), QPointF(gr.right(), y))
            # Vertical lines
            x = gr.left() + i * (gr.width() / 8.0)
            painter.drawLine(QPointF(x, gr.top()), QPointF(x, gr.bottom()))

        # 3. Y-Axis Labels (Left of box: "Max" at top, "RPM" in middle, "Min" at bottom)
        label_font = QFont("Inter", 8)
        painter.setFont(label_font)
        painter.setPen(QColor("#888888"))

        # "Max" at top
        painter.drawText(
            QRectF(0, gr.top() - 4, gr.left() - 6, 16),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            "Max",
        )
        # "RPM" in middle
        painter.drawText(
            QRectF(0, gr.center().y() - 8, gr.left() - 6, 16),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            "RPM",
        )
        # "Min" at bottom
        painter.drawText(
            QRectF(0, gr.bottom() - 12, gr.left() - 6, 16),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            "Min",
        )

        # 4. X-Axis Labels (Below box: "50°C" at left corner, "Temperature" in middle, "90°C" at right)
        painter.drawText(
            QRectF(gr.left() - 5, gr.bottom() + 6, 50, 16),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
            "50°C",
        )
        painter.drawText(
            QRectF(gr.left(), gr.bottom() + 6, gr.width(), 16),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
            "Temperature",
        )
        painter.drawText(
            QRectF(gr.right() - 45, gr.bottom() + 6, 50, 16),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop,
            "90°C",
        )

        # 5. Continuous Blue Polyline (#2563EB, 2.5px) with Lead-in / Lead-out
        pixel_nodes = [self._temp_speed_to_pixel(n[0], n[1]) for n in self._nodes]

        if pixel_nodes:
            curve_path = QPainterPath()
            # Lead-in horizontal line from left border of graph to first node
            curve_path.moveTo(gr.left(), pixel_nodes[0].y())
            for pt in pixel_nodes:
                curve_path.lineTo(pt)
            # Lead-out horizontal line from last node to right border of graph
            curve_path.lineTo(gr.right(), pixel_nodes[-1].y())

            line_pen = QPen(QColor("#2563EB"), 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            painter.setPen(line_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(curve_path)

        # 6. Nodes Rendering (Glowing light-grey/white circle radius 3.5px with outer blue halo radius 6.5px)
        for idx, pt in enumerate(pixel_nodes):
            is_hovered = (idx == self._hovered_node_idx)
            is_dragged = (idx == self._dragged_node_idx)

            halo_radius = 7.5 if (is_hovered or is_dragged) else 6.0
            halo_color = QColor("#60A5FA") if (is_hovered or is_dragged) else QColor("#3B82F6")

            # Outer Halo
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(halo_color))
            painter.drawEllipse(pt, halo_radius, halo_radius)

            # Inner Circle
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor("#E2E8F0")))
            painter.drawEllipse(pt, 3.5, 3.5)

    # ── Mouse Interaction ────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()
            pixel_nodes = [self._temp_speed_to_pixel(n[0], n[1]) for n in self._nodes]
            for idx, pt in enumerate(pixel_nodes):
                dist = (pt.x() - pos.x()) ** 2 + (pt.y() - pos.y()) ** 2
                if dist <= 12 ** 2:
                    self._dragged_node_idx = idx
                    self.update()
                    break

    def mouseMoveEvent(self, event):
        pos = event.position()
        if self._dragged_node_idx is not None:
            idx = self._dragged_node_idx
            new_speed = self._pixel_to_speed(pos.y())
            clamped_speed = max(0.0, min(100.0, round(new_speed, 1)))

            # Monotonic constraints: node cannot be lower than left node, nor higher than right node
            min_s = self._nodes[idx - 1][1] if idx > 0 else 0.0
            max_s = self._nodes[idx + 1][1] if idx < len(self._nodes) - 1 else 100.0

            # Allow user to push neighbors or enforce clamp:
            # Let's enforce monotonic non-decreasing clamp:
            smooth_speed = max(min_s, min(max_s, clamped_speed))
            self._nodes[idx][1] = smooth_speed

            self.update()
        else:
            prev_hover = self._hovered_node_idx
            self._hovered_node_idx = None
            pixel_nodes = [self._temp_speed_to_pixel(n[0], n[1]) for n in self._nodes]
            for idx, pt in enumerate(pixel_nodes):
                dist = (pt.x() - pos.x()) ** 2 + (pt.y() - pos.y()) ** 2
                if dist <= 12 ** 2:
                    self._hovered_node_idx = idx
                    break
            if prev_hover != self._hovered_node_idx:
                self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._dragged_node_idx is not None:
            self._dragged_node_idx = None
            self.update()
            self.curveChanged.emit(self.get_curve())
