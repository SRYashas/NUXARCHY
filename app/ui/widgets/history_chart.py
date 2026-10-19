"""
Real-Time Telemetry History Chart Widget
Renders dynamic rolling telemetry curves with antialiased lines and glowing gradient fills.
"""

from collections import deque
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QLinearGradient, QPainterPath, QFont
from PySide6.QtCore import Qt, QPointF


class HistoryChartWidget(QFrame):
    def __init__(self, title: str = "SYSTEM UTILIZATION OVER TIME", max_points: int = 60, parent=None):
        super().__init__(parent)
        self.setObjectName("historyChart")
        self.setProperty("class", "cardFrame")
        self.max_points = max_points
        self.cpu_history = deque(maxlen=max_points)
        self.gpu_history = deque(maxlen=max_points)

        # Pre-fill with zeroes
        for _ in range(max_points):
            self.cpu_history.append(0.0)
            self.gpu_history.append(0.0)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        # Header with legend
        header = QHBoxLayout()
        title_label = QLabel(title.upper())
        title_label.setProperty("class", "cardTitle")
        header.addWidget(title_label)

        header.addStretch()

        # Legend CPU
        leg_cpu = QLabel("■ CPU %")
        leg_cpu.setStyleSheet("color: #00FFD1; font-weight: 700; font-size: 11px;")
        header.addWidget(leg_cpu)

        # Legend GPU
        leg_gpu = QLabel("■ NVIDIA GPU %")
        leg_gpu.setStyleSheet("color: #9D4EDD; font-weight: 700; font-size: 11px;")
        header.addWidget(leg_gpu)

        layout.addLayout(header)

        # Canvas widget that handles the paintEvent
        self.canvas = _ChartCanvas(self.cpu_history, self.gpu_history)
        layout.addWidget(self.canvas)

    def add_sample(self, cpu_val: float, gpu_val: float):
        self.cpu_history.append(max(0.0, min(100.0, cpu_val or 0.0)))
        self.gpu_history.append(max(0.0, min(100.0, gpu_val or 0.0)))
        self.canvas.update()


class _ChartCanvas(QWidget):
    def __init__(self, cpu_history: deque, gpu_history: deque, parent=None):
        super().__init__(parent)
        self.cpu_history = cpu_history
        self.gpu_history = gpu_history
        self.setMinimumHeight(140)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Draw grid lines (0%, 25%, 50%, 75%, 100%)
        grid_pen = QPen(QColor(35, 39, 52), 1, Qt.DashLine)
        painter.setPen(grid_pen)

        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)

        for step in [0.25, 0.50, 0.75]:
            y = int(h * (1.0 - step))
            painter.drawLine(0, y, w, y)
            painter.setPen(QColor(107, 114, 128))
            painter.drawText(4, y - 2, f"{int(step * 100)}%")
            painter.setPen(grid_pen)

        pts_count = len(self.cpu_history)
        if pts_count < 2:
            return

        dx = w / (pts_count - 1)

        # Draw GPU series (Violet)
        self._draw_series(
            painter, self.gpu_history, dx, h,
            line_color=QColor(157, 78, 221),
            grad_color=QColor(157, 78, 221, 40)
        )

        # Draw CPU series (Electric Turquoise)
        self._draw_series(
            painter, self.cpu_history, dx, h,
            line_color=QColor(0, 255, 209),
            grad_color=QColor(0, 255, 209, 45)
        )

    def _draw_series(self, painter: QPainter, series: deque, dx: float, h: float, line_color: QColor, grad_color: QColor):
        path = QPainterPath()
        fill_path = QPainterPath()

        start_y = h * (1.0 - (series[0] / 100.0))
        path.moveTo(0, start_y)
        fill_path.moveTo(0, h)
        fill_path.lineTo(0, start_y)

        for i, val in enumerate(series):
            x = i * dx
            y = h * (1.0 - (val / 100.0))
            path.lineTo(x, y)
            fill_path.lineTo(x, y)

        fill_path.lineTo((len(series) - 1) * dx, h)
        fill_path.closeSubpath()

        # Fill gradient
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.0, grad_color)
        grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.fillPath(fill_path, QBrush(grad))

        # Stroke line
        pen = QPen(line_color, 2.0)
        painter.setPen(pen)
        painter.drawPath(path)
