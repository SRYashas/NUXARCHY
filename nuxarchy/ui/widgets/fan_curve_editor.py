"""
NUXARCHY Interactive Fan Curve Editor Widget
Interactive 2D coordinate grid with draggable control nodes, monotonic constraints,
gradient area fill, grid lines, and live real-time temperature tracking line.
"""

from typing import List, Tuple, Optional
from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPainterPath, QLinearGradient
from PyQt6.QtWidgets import QWidget


class FanCurveEditor(QWidget):
    """Interactive 2D Spline / Piecewise Linear Fan Curve Editor."""

    curveChanged = pyqtSignal(list)

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setMinimumSize(420, 260)
        self.setMouseTracking(True)

        # Temperature limits (X: 30°C to 100°C) and Speed limits (Y: 0% to 100%)
        self.min_temp = 30.0
        self.max_temp = 100.0
        self.min_speed = 0.0
        self.max_speed = 100.0

        # Control nodes: list of [temp_c, speed_pct]
        self._nodes: List[List[float]] = [
            [30.0, 20.0],
            [45.0, 35.0],
            [60.0, 50.0],
            [75.0, 75.0],
            [85.0, 100.0],
        ]

        # Dragging state
        self._dragged_node_idx: Optional[int] = None
        self._hovered_node_idx: Optional[int] = None

        # Live temperature indicator
        self._current_temp: float = 45.0

    def set_curve(self, points: List[Tuple[float, float]]):
        if len(points) >= 2:
            self._nodes = [[float(p[0]), float(p[1])] for p in points]
            self._nodes.sort(key=lambda p: p[0])
            self.update()

    def get_curve(self) -> List[Tuple[float, float]]:
        return [(p[0], p[1]) for p in self._nodes]

    def set_current_temperature(self, temp: float):
        self._current_temp = float(temp)
        self.update()

    # ── Coordinate Transforms ────────────────────────────────────────────────

    def _graph_rect(self) -> QRectF:
        pad_left = 50.0
        pad_right = 25.0
        pad_top = 20.0
        pad_bottom = 35.0
        return QRectF(
            pad_left,
            pad_top,
            max(50.0, self.width() - pad_left - pad_right),
            max(50.0, self.height() - pad_top - pad_bottom),
        )

    def _temp_speed_to_pixel(self, temp: float, speed: float) -> QPointF:
        gr = self._graph_rect()
        x_pct = (temp - self.min_temp) / (self.max_temp - self.min_temp)
        y_pct = (speed - self.min_speed) / (self.max_speed - self.min_speed)
        px = gr.left() + x_pct * gr.width()
        py = gr.bottom() - y_pct * gr.height()
        return QPointF(px, py)

    def _pixel_to_temp_speed(self, pos: QPointF) -> Tuple[float, float]:
        gr = self._graph_rect()
        x_pct = max(0.0, min(1.0, (pos.x() - gr.left()) / gr.width()))
        y_pct = max(0.0, min(1.0, (gr.bottom() - pos.y()) / gr.height()))
        temp = self.min_temp + x_pct * (self.max_temp - self.min_temp)
        speed = self.min_speed + y_pct * (self.max_speed - self.min_speed)
        return temp, speed

    # ── Paint Event ──────────────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        gr = self._graph_rect()

        # Canvas Background
        painter.fillRect(gr, QColor("#12141C"))
        painter.setPen(QPen(QColor("#222533"), 1))
        painter.drawRect(gr)

        # 1. Subtle Dark Grid Lines (#1E2230)
        grid_pen = QPen(QColor("#1E2230"), 1, Qt.PenStyle.DashLine)
        painter.setPen(grid_pen)
        painter.setFont(QFont("Inter", 8))

        # Horizontal Grid (Speed: 25%, 50%, 75%, 100%)
        for s in (25, 50, 75, 100):
            p = self._temp_speed_to_pixel(self.min_temp, s)
            painter.drawLine(int(gr.left()), int(p.y()), int(gr.right()), int(p.y()))
            painter.setPen(QColor("#6A7085"))
            painter.drawText(
                QRectF(0, p.y() - 8, gr.left() - 8, 16),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                f"{s}%",
            )
            painter.setPen(grid_pen)

        # Vertical Grid (Temp: 40, 50, 60, 70, 80, 90, 100°C)
        for t in range(40, 101, 10):
            p = self._temp_speed_to_pixel(t, self.min_speed)
            painter.drawLine(int(p.x()), int(gr.top()), int(p.x()), int(gr.bottom()))
            painter.setPen(QColor("#6A7085"))
            painter.drawText(
                QRectF(p.x() - 20, gr.bottom() + 6, 40, 20),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                f"{t}°C",
            )
            painter.setPen(grid_pen)

        # 2. Live Current Temp Indicator (Vertical dashed neon cyan line)
        if self.min_temp <= self._current_temp <= self.max_temp:
            live_p = self._temp_speed_to_pixel(self._current_temp, 0)
            indicator_pen = QPen(QColor("#00E5FF"), 1.5, Qt.PenStyle.DashDotLine)
            painter.setPen(indicator_pen)
            painter.drawLine(int(live_p.x()), int(gr.top()), int(live_p.x()), int(gr.bottom()))

            # Small live label pill
            pill_rect = QRectF(live_p.x() - 22, gr.top() - 16, 44, 15)
            painter.setBrush(QBrush(QColor("#00E5FF")))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(pill_rect, 3, 3)
            painter.setPen(QColor("#0A0B10"))
            painter.setFont(QFont("Inter", 7, QFont.Weight.Bold))
            painter.drawText(pill_rect, Qt.AlignmentFlag.AlignCenter, f"{int(self._current_temp)}°C")

        # 3. Semi-transparent gradient fill under the curve (rgba(0, 229, 255, 0.15))
        curve_path = QPainterPath()
        pixel_nodes = [self._temp_speed_to_pixel(n[0], n[1]) for n in self._nodes]

        if pixel_nodes:
            curve_path.moveTo(gr.left(), pixel_nodes[0].y())
            for pt in pixel_nodes:
                curve_path.lineTo(pt)
            curve_path.lineTo(gr.right(), pixel_nodes[-1].y())

            fill_path = QPainterPath(curve_path)
            fill_path.lineTo(gr.right(), gr.bottom())
            fill_path.lineTo(gr.left(), gr.bottom())
            fill_path.closeSubpath()

            grad = QLinearGradient(gr.topLeft(), gr.bottomLeft())
            grad.setColorAt(0.0, QColor(0, 229, 255, 60))
            grad.setColorAt(1.0, QColor(0, 229, 255, 5))
            painter.setBrush(QBrush(grad))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPath(fill_path)

            # Curve Stroke
            stroke_pen = QPen(QColor("#00E5FF"), 2.5)
            painter.setPen(stroke_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(curve_path)

        # 4. Draggable Control Nodes (radius 8px, #00E5FF fill, hover glow #FF0552)
        node_radius = 7.0
        for idx, pt in enumerate(pixel_nodes):
            is_hovered = idx == self._hovered_node_idx
            is_dragged = idx == self._dragged_node_idx

            if is_hovered or is_dragged:
                # Outer glow
                glow_color = QColor(255, 5, 82, 120)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(glow_color))
                painter.drawEllipse(pt, node_radius + 4, node_radius + 4)
                node_color = QColor("#FF0552")
            else:
                node_color = QColor("#00E5FF")

            # Inner circle
            painter.setPen(QPen(QColor("#FFFFFF"), 1.5))
            painter.setBrush(QBrush(node_color))
            painter.drawEllipse(pt, node_radius, node_radius)

    # ── Mouse Interaction & Monotonic Constraints ────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()
            # Check if clicked on any node
            for idx, n in enumerate(self._nodes):
                pt = self._temp_speed_to_pixel(n[0], n[1])
                dist = (pt.x() - pos.x()) ** 2 + (pt.y() - pos.y()) ** 2
                if dist <= 12 ** 2:
                    self._dragged_node_idx = idx
                    self.update()
                    break

    def mouseMoveEvent(self, event):
        pos = event.position()
        if self._dragged_node_idx is not None:
            idx = self._dragged_node_idx
            new_temp, new_speed = self._pixel_to_temp_speed(pos)

            # Monotonic Constraints: Node i cannot cross node i-1 or node i+1 horizontally
            min_t = self._nodes[idx - 1][0] + 1.0 if idx > 0 else self.min_temp
            max_t = self._nodes[idx + 1][0] - 1.0 if idx < len(self._nodes) - 1 else self.max_temp

            clamped_temp = max(min_t, min(max_t, new_temp))
            clamped_speed = max(0.0, min(100.0, new_speed))

            self._nodes[idx] = [round(clamped_temp, 1), round(clamped_speed, 1)]
            self.update()
        else:
            # Update hover state
            prev_hover = self._hovered_node_idx
            self._hovered_node_idx = None
            for idx, n in enumerate(self._nodes):
                pt = self._temp_speed_to_pixel(n[0], n[1])
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
