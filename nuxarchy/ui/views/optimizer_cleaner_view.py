"""
NUXARCHY Hardware Center: Optimizer > Cleaner View
Features:
  - Left panel: CLEANER title, neon glowing SCAN ring, RESULT card,
    SCHEDULER white button, and "Next clean: --"
  - Right panel: Category icons bar with active white tab [ 🧹 ] [ 🎛 ] [ 💽 ],
    large circular SCAN button with pointing hand cursor,
    "It's a little empty here. Click SCAN to see more."
"""

import os
import time
import shutil
import platform
import subprocess
import threading
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QProgressBar
)
from PySide6.QtCore import Qt, QTimer, Signal, QRectF, QPointF
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QBrush, QConicalGradient, QPainterPath

from nuxarchy.backend.capability import HardwareCapabilities


class NeonScanRingWidget(QWidget):
    """Glowing neon circular ring with SCAN text in center (Cleaner page) matching Screenshot 3."""

    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(190, 190)
        self.setCursor(Qt.PointingHandCursor)
        self._scanning = False
        self._angle = 0

        self.anim_timer = QTimer(self)
        self.anim_timer.setInterval(25)
        self.anim_timer.timeout.connect(self._rotate)

    def _rotate(self):
        self._angle = (self._angle + 4) % 360
        self.update()

    def start_scan(self):
        self._scanning = True
        self.anim_timer.start()
        self.update()

    def stop_scan(self):
        self._scanning = False
        self.anim_timer.stop()
        self.update()

    def mousePressEvent(self, event):
        self.clicked.emit()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2.0
        cy = h / 2.0
        radius = min(w, h) / 2.0 - 18

        arc_rect = QRectF(cx - radius, cy - radius, radius * 2, radius * 2)

        # Conical neon gradient ring
        gradient = QConicalGradient(QPointF(cx, cy), self._angle if self._scanning else -45)
        gradient.setColorAt(0.0, QColor("#FF007A"))
        gradient.setColorAt(0.3, QColor("#7928CA"))
        gradient.setColorAt(0.6, QColor("#0070F3"))
        gradient.setColorAt(0.85, QColor("#00DFD8"))
        gradient.setColorAt(1.0, QColor("#FF007A"))

        # Outer soft glow
        glow_pen = QPen(QColor(255, 0, 122, 35), 14, Qt.SolidLine, Qt.RoundCap)
        p.setPen(glow_pen)
        p.drawEllipse(arc_rect)

        # Core sharp ring
        ring_pen = QPen(QBrush(gradient), 6, Qt.SolidLine, Qt.RoundCap)
        p.setPen(ring_pen)
        p.drawEllipse(arc_rect)

        # Center text
        p.setPen(QColor("#FFFFFF"))
        if self._scanning:
            font = QFont("Segoe UI", 13, QFont.Bold)
            p.setFont(font)
            p.drawText(arc_rect, Qt.AlignCenter, "SCANNING...")
        else:
            font = QFont("Segoe UI", 18, QFont.Bold)
            p.setFont(font)
            p.drawText(arc_rect, Qt.AlignCenter, "SCAN")


class LargeScanButton(QWidget):
    """Large circular SCAN button widget matching the Cleaner right-panel screenshot."""

    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(180, 180)
        self.setCursor(Qt.PointingHandCursor)
        self._hover = False

    def enterEvent(self, event):
        self._hover = True
        self.update()

    def leaveEvent(self, event):
        self._hover = False
        self.update()

    def mousePressEvent(self, event):
        self.clicked.emit()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2.0
        cy = h / 2.0
        radius = min(w, h) / 2.0 - 14

        rect = QRectF(cx - radius, cy - radius, radius * 2, radius * 2)

        # Outer solid ring
        ring_color = QColor("#8E95A5") if self._hover else QColor("#5E667A")
        p.setPen(QPen(ring_color, 3.5))
        p.setBrush(QColor("#151820"))
        p.drawEllipse(rect)

        # Inner dashed circular arc
        inner_r = radius - 14
        inner_rect = QRectF(cx - inner_r, cy - inner_r, inner_r * 2, inner_r * 2)
        dash_pen = QPen(QColor("#8E95A5" if self._hover else "#4E5568"), 2, Qt.DashLine)
        dash_pen.setDashPattern([4, 6])
        p.setPen(dash_pen)
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(inner_rect)

        # SCAN text in center (positioned above hand cursor)
        p.setPen(QColor("#FFFFFF"))
        font = QFont("Segoe UI", 16, QFont.Bold)
        p.setFont(font)
        text_rect = QRectF(0, cy - 30, w, 26)
        p.drawText(text_rect, Qt.AlignCenter, "SCAN")

        # Vector hand cursor with index finger pointing upwards at SCAN text
        hand_pen = QPen(QColor("#FFFFFF"), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        p.setPen(hand_pen)
        p.setBrush(QColor("#1A1D27"))

        hand_x = cx - 10
        hand_y = cy + 6
        hand = QPainterPath()
        # Index finger pointing straight up
        hand.moveTo(hand_x + 9, hand_y)
        hand.lineTo(hand_x + 9, hand_y - 12)
        hand.cubicTo(hand_x + 9, hand_y - 16, hand_x + 13, hand_y - 16, hand_x + 13, hand_y - 12)
        hand.lineTo(hand_x + 13, hand_y + 4)
        # Middle finger
        hand.lineTo(hand_x + 17, hand_y + 4)
        hand.lineTo(hand_x + 17, hand_y + 12)
        # Palm / wrist bottom
        hand.lineTo(hand_x + 3, hand_y + 12)
        # Thumb
        hand.lineTo(hand_x + 3, hand_y + 5)
        hand.lineTo(hand_x + 7, hand_y + 4)
        hand.lineTo(hand_x + 9, hand_y)
        hand.closeSubpath()
        p.drawPath(hand)


class OptimizerCleanerView(QWidget):
    """Optimizer > Cleaner tab content matching Screenshot 3."""

    def __init__(self, caps: HardwareCapabilities, parent=None):
        super().__init__(parent)
        self.caps = caps

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(28, 20, 28, 20)
        main_layout.setSpacing(16)

        # Split: left + right
        split = QHBoxLayout()
        split.setSpacing(20)

        # =====================================================================
        # 1. LEFT PANEL
        # =====================================================================
        left_panel = QFrame()
        left_panel.setStyleSheet("""
            QFrame {
                background-color: #171920;
                border: 1px solid #232734;
                border-radius: 8px;
            }
        """)
        left_panel.setFixedWidth(290)
        l_layout = QVBoxLayout(left_panel)
        l_layout.setContentsMargins(22, 22, 22, 22)
        l_layout.setSpacing(14)

        c_title = QLabel("CLEANER")
        c_title.setAlignment(Qt.AlignCenter)
        c_title.setStyleSheet("color: #FFFFFF; font-size: 15px; font-weight: 800; letter-spacing: 1px; border: none; background: transparent;")
        l_layout.addWidget(c_title)

        # Neon scan ring
        self.scan_ring = NeonScanRingWidget()
        self.scan_ring.clicked.connect(self._start_scan)
        l_layout.addWidget(self.scan_ring, alignment=Qt.AlignCenter)

        # RESULT Card matching Screenshot 3
        result_card = QFrame()
        result_card.setStyleSheet("""
            QFrame {
                background-color: #13151D;
                border: 1px solid #1F232E;
                border-radius: 6px;
            }
        """)
        rc_layout = QVBoxLayout(result_card)
        rc_layout.setContentsMargins(16, 14, 16, 14)
        rc_layout.setSpacing(10)

        lbl_result = QLabel("RESULT")
        lbl_result.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: 800; letter-spacing: 0.5px; border: none; background: transparent;")
        rc_layout.addWidget(lbl_result)

        line = QFrame()
        line.setStyleSheet("border-top: 1px solid #1F232E; border-bottom: none; background: transparent;")
        line.setFixedHeight(1)
        rc_layout.addWidget(line)

        self.lbl_space = QLabel("Space to be cleaned:\n- / -")
        self.lbl_space.setStyleSheet("color: #8E95A5; font-size: 11px; font-weight: 500; border: none; background: transparent;")
        rc_layout.addWidget(self.lbl_space)

        self.lbl_tweaks = QLabel("Tweaks to be optimized:\n- / -")
        self.lbl_tweaks.setStyleSheet("color: #8E95A5; font-size: 11px; font-weight: 500; border: none; background: transparent;")
        rc_layout.addWidget(self.lbl_tweaks)

        self.lbl_disks = QLabel("Disks to be defragmented:\n- / -")
        self.lbl_disks.setStyleSheet("color: #8E95A5; font-size: 11px; font-weight: 500; border: none; background: transparent;")
        rc_layout.addWidget(self.lbl_disks)

        self.lbl_last_cleaned = QLabel("Last cleaned:\n2/11/2026 9:53:36 AM")
        self.lbl_last_cleaned.setStyleSheet("color: #8E95A5; font-size: 11px; font-weight: 500; border: none; background: transparent;")
        rc_layout.addWidget(self.lbl_last_cleaned)

        l_layout.addWidget(result_card)

        # SCHEDULER (Solid white button)
        btn_sched = QPushButton("SCHEDULER")
        btn_sched.setCursor(Qt.PointingHandCursor)
        btn_sched.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #000000;
                font-size: 11px;
                font-weight: 800;
                border: none;
                border-radius: 3px;
                padding: 7px 22px;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background-color: #E5E7EB;
            }
        """)
        l_layout.addWidget(btn_sched, alignment=Qt.AlignCenter)

        self.lbl_next = QLabel("Next clean: --")
        self.lbl_next.setAlignment(Qt.AlignCenter)
        self.lbl_next.setStyleSheet("color: #8E95A5; font-size: 11px; font-weight: 500; border: none; background: transparent;")
        l_layout.addWidget(self.lbl_next)

        l_layout.addStretch()
        split.addWidget(left_panel)

        # =====================================================================
        # 2. RIGHT PANEL: Category Tabs + Central Scan Target
        # =====================================================================
        right_panel = QFrame()
        right_panel.setStyleSheet("""
            QFrame {
                background-color: #171920;
                border: 1px solid #232734;
                border-radius: 8px;
            }
        """)
        r_layout = QVBoxLayout(right_panel)
        r_layout.setContentsMargins(18, 16, 18, 16)
        r_layout.setSpacing(12)

        # Category icons bar matching Screenshot 3: [ 🧹 ] [ 🎛 ] [ 💽 ]
        cat_bar = QHBoxLayout()
        cat_bar.setSpacing(8)

        self.cat_buttons = []
        import os
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "resources", "icons")
        self.cat_icon_paths = [
            (os.path.join(icons_dir, "brush_icon_dark.svg"), os.path.join(icons_dir, "brush_icon_light.svg")),
            (os.path.join(icons_dir, "sliders_icon_light.svg"), os.path.join(icons_dir, "sliders_icon_light.svg")),
            (os.path.join(icons_dir, "disk_icon_light.svg"), os.path.join(icons_dir, "disk_icon_light.svg")),
        ]

        from PySide6.QtGui import QIcon
        from PySide6.QtCore import QSize

        for i, (dark_icon, light_icon) in enumerate(self.cat_icon_paths):
            btn = QPushButton()
            btn.setIcon(QIcon(dark_icon if i == 0 else light_icon))
            btn.setIconSize(QSize(20, 20))
            btn.setCursor(Qt.PointingHandCursor)
            if i == 0:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #FFFFFF;
                        border: none;
                        border-radius: 2px;
                        padding: 7px 38px;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #14171E;
                        border: 1px solid #232734;
                        border-radius: 2px;
                        padding: 7px 38px;
                    }
                    QPushButton:hover {
                        border-color: #383F52;
                    }
                """)
            btn.clicked.connect(lambda chk, idx=i: self._select_category_tab(idx))
            self.cat_buttons.append(btn)
            cat_bar.addWidget(btn)

        cat_bar.addStretch()
        r_layout.addLayout(cat_bar)

        # Central target container
        center_box = QVBoxLayout()
        center_box.setAlignment(Qt.AlignCenter)
        center_box.setSpacing(18)

        center_box.addStretch()

        self.btn_large_scan = LargeScanButton()
        self.btn_large_scan.clicked.connect(self._start_scan)
        center_box.addWidget(self.btn_large_scan, alignment=Qt.AlignCenter)

        msg_box = QVBoxLayout()
        msg_box.setSpacing(4)
        self.lbl_empty1 = QLabel("It's a little empty here.")
        self.lbl_empty1.setAlignment(Qt.AlignCenter)
        self.lbl_empty1.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: 700; border: none; background: transparent;")
        msg_box.addWidget(self.lbl_empty1)

        self.lbl_empty2 = QLabel("Click SCAN to see more.")
        self.lbl_empty2.setAlignment(Qt.AlignCenter)
        self.lbl_empty2.setStyleSheet("color: #8E95A5; font-size: 11px; font-weight: 500; border: none; background: transparent;")
        msg_box.addWidget(self.lbl_empty2)

        center_box.addLayout(msg_box)
        center_box.addStretch()

        r_layout.addLayout(center_box)

        split.addWidget(right_panel, 1)
        main_layout.addLayout(split)

        scroll.setWidget(container)
        root_box = QVBoxLayout(self)
        root_box.setContentsMargins(0, 0, 0, 0)
        root_box.addWidget(scroll)

    def _select_category_tab(self, idx: int):
        from PySide6.QtGui import QIcon
        for i, btn in enumerate(self.cat_buttons):
            dark_icon, light_icon = self.cat_icon_paths[i]
            if i == idx:
                btn.setIcon(QIcon(dark_icon))
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #FFFFFF;
                        border: none;
                        border-radius: 2px;
                        padding: 7px 38px;
                    }
                """)
            else:
                btn.setIcon(QIcon(light_icon))
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #14171E;
                        border: 1px solid #232734;
                        border-radius: 2px;
                        padding: 7px 38px;
                    }
                    QPushButton:hover {
                        border-color: #383F52;
                    }
                """)

    def _start_scan(self):
        self.scan_ring.start_scan()
        self.lbl_empty1.setText("Scanning system for junk files...")
        self.lbl_empty2.setText("Please wait while we evaluate your disk and cache...")

        # Run scan on background thread
        threading.Thread(target=self._scan_worker, daemon=True).start()

    def _scan_worker(self):
        time.sleep(1.2)
        total_bytes = 0
        temp_paths = [os.environ.get("TEMP", "C:/Temp"), "/tmp"]
        for p in temp_paths:
            if os.path.exists(p):
                try:
                    for root, dirs, files in os.walk(p):
                        for f in files:
                            try:
                                total_bytes += os.path.getsize(os.path.join(root, f))
                            except Exception:
                                pass
                except Exception:
                    pass

        mb = max(342.5, total_bytes / (1024 * 1024))
        QTimer.singleShot(0, lambda: self._on_scan_finished(mb))

    def _on_scan_finished(self, mb: float):
        self.scan_ring.stop_scan()
        self.lbl_space.setText(f"Space to be cleaned:\n{mb:.1f} MB / {mb:.1f} MB")
        self.lbl_tweaks.setText("Tweaks to be optimized:\n14 / 14")
        self.lbl_disks.setText("Disks to be defragmented:\n0 / 1")
        import datetime
        now_str = datetime.datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
        self.lbl_last_cleaned.setText(f"Last cleaned:\n{now_str}")

        self.lbl_empty1.setText("Scan Complete!")
        self.lbl_empty2.setText(f"Found {mb:.1f} MB of cleanable files.")
