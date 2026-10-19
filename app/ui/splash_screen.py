"""
NUXARCHY: Cinematic Cyber Splash & Loading Screen
Displays the NUXARCHY logo on a pure black screen with cyberpunk typography,
hardware initialization telemetry, and smooth fade transitions.
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QProgressBar, QGraphicsOpacityEffect, QApplication
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Signal, QRect
from PySide6.QtGui import QPixmap, QFont, QColor, QPainter, QGuiApplication


class SplashScreen(QWidget):
    """Full-screen / cinematic centered splash screen on pure black background."""

    finished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # Frameless, translucent black window
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setStyleSheet("background-color: #000000;")

        # Screen dimensions
        screen = QGuiApplication.primaryScreen().geometry()
        width = 620
        height = 540
        self.setGeometry(
            (screen.width() - width) // 2,
            (screen.height() - height) // 2,
            width,
            height
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 48, 40, 40)
        layout.setSpacing(14)
        layout.setAlignment(Qt.AlignCenter)

        # 1. NUXARCHY Logo
        self.lbl_logo = QLabel()
        self.lbl_logo.setAlignment(Qt.AlignCenter)
        self.lbl_logo.setStyleSheet("background: transparent; border: none;")

        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "nuxarchy_logo.png")
        if os.path.exists(logo_path):
            pix = QPixmap(logo_path)
            pix = pix.scaled(260, 260, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.lbl_logo.setPixmap(pix)
        layout.addWidget(self.lbl_logo)

        layout.addSpacing(6)

        # 2. "NUXARCHY" Title with Cyberpunk Green / Arch Styling
        lbl_title = QLabel("NUXARCHY")
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet("""
            QLabel {
                color: #00FF85;
                font-family: 'Segoe UI', 'Inter', 'Outfit', sans-serif;
                font-size: 32px;
                font-weight: 900;
                letter-spacing: 8px;
                background: transparent;
                border: none;
            }
        """)
        layout.addWidget(lbl_title)

        # Subtitle
        lbl_sub = QLabel("ARCH LINUX GAMING & HARDWARE CONTROL")
        lbl_sub.setAlignment(Qt.AlignCenter)
        lbl_sub.setStyleSheet("""
            QLabel {
                color: #8E95A5;
                font-family: 'Segoe UI', sans-serif;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 3px;
                background: transparent;
                border: none;
            }
        """)
        layout.addWidget(lbl_sub)

        layout.addSpacing(16)

        # 3. Cyberpunk Progress Bar
        self.progress = QProgressBar()
        self.progress.setFixedWidth(360)
        self.progress.setFixedHeight(4)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar {
                background-color: #12141A;
                border: 1px solid #1C202B;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00FF85, stop:0.5 #00DFD8, stop:1 #0078D4);
                border-radius: 2px;
            }
        """)
        layout.addWidget(self.progress, alignment=Qt.AlignCenter)

        # 4. Status Text
        self.lbl_status = QLabel("INITIALIZING NUXARCHY CORE...")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setStyleSheet("""
            QLabel {
                color: #4B5563;
                font-family: 'Segoe UI', monospace;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 1.5px;
                background: transparent;
                border: none;
            }
        """)
        layout.addWidget(self.lbl_status)

        # Opacity effect for smooth fade in/out
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0.0)

        # Fade in animation
        self.anim_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim_in.setDuration(400)
        self.anim_in.setStartValue(0.0)
        self.anim_in.setEndValue(1.0)
        self.anim_in.setEasingCurve(QEasingCurve.OutCubic)

        # Steps animation timer
        self._step = 0
        self._steps = [
            (20, "INITIALIZING HARDWARE PROBES..."),
            (45, "CONNECTING EC & FAN CONTROLLERS..."),
            (70, "LOADING LIGHTING & THERMAL PROFILES..."),
            (90, "INITIALIZING GPU POWER SWITCHER..."),
            (100, "NUXARCHY SYSTEM READY"),
        ]

        self.timer = QTimer(self)
        self.timer.setInterval(220)
        self.timer.timeout.connect(self._on_tick)

    def start_loading(self):
        """Shows splash screen and begins progress animation."""
        self.show()
        self.anim_in.start()
        self.timer.start()

    def _on_tick(self):
        if self._step < len(self._steps):
            pct, msg = self._steps[self._step]
            self.progress.setValue(pct)
            self.lbl_status.setText(msg)
            self._step += 1
        else:
            self.timer.stop()
            # Fade out
            QTimer.singleShot(250, self._fade_out)

    def _fade_out(self):
        self.anim_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim_out.setDuration(350)
        self.anim_out.setStartValue(1.0)
        self.anim_out.setEndValue(0.0)
        self.anim_out.setEasingCurve(QEasingCurve.InCubic)
        self.anim_out.finished.connect(self._on_finished)
        self.anim_out.start()

    def _on_finished(self):
        self.close()
        self.finished.emit()
