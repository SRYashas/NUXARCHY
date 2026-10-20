"""
NUXARCHY Glow Card Widget
Selectable QFrame card with neon glowing borders, dynamic QGraphicsDropShadowEffect,
title, subtitle, icon glyph, and status badge.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QGraphicsDropShadowEffect,
    QWidget,
)


class GlowCard(QFrame):
    """Production selectable card widget with OMEN neon borders and shadow glow."""

    clicked = pyqtSignal()

    def __init__(
        self,
        title: str,
        subtitle: str = "",
        icon_text: str = "⚡",
        badge_text: str = "",
        accent_color: str = "#00E5FF",
        parent: QWidget = None,
    ):
        super().__init__(parent)
        self.title = title
        self.subtitle = subtitle
        self.icon_text = icon_text
        self.badge_text = badge_text
        self.accent_color = accent_color
        self._active: bool = False

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._setup_ui()
        self._setup_shadow()
        self.set_active(False)

    def _setup_ui(self):
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumHeight(110)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)

        # Header: Icon + Badge
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)

        self.icon_lbl = QLabel(self.icon_text)
        self.icon_lbl.setFont(QFont("Segoe UI Emoji", 18))
        header.addWidget(self.icon_lbl)

        header.addStretch()

        self.badge_lbl = QLabel(self.badge_text)
        self.badge_lbl.setFont(QFont("Inter", 8, QFont.Weight.Bold))
        self.badge_lbl.setStyleSheet(
            f"background-color: #1C1F2E; color: {self.accent_color}; "
            "padding: 3px 8px; border-radius: 4px; border: 1px solid #2B3045;"
        )
        if not self.badge_text:
            self.badge_lbl.hide()
        header.addWidget(self.badge_lbl)

        layout.addLayout(header)

        # Title
        self.title_lbl = QLabel(self.title.upper())
        title_font = QFont("Inter", 11, QFont.Weight.Bold)
        title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.2)
        self.title_lbl.setFont(title_font)
        self.title_lbl.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(self.title_lbl)

        # Subtitle
        self.subtitle_lbl = QLabel(self.subtitle)
        self.subtitle_lbl.setFont(QFont("Inter", 9))
        self.subtitle_lbl.setStyleSheet("color: #8E92A4;")
        self.subtitle_lbl.setWordWrap(True)
        layout.addWidget(self.subtitle_lbl)

    def _setup_shadow(self):
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(20)
        self._shadow.setColor(QColor(self.accent_color))
        self._shadow.setOffset(0, 0)
        self._shadow.setEnabled(False)
        self.setGraphicsEffect(self._shadow)

    def set_active(self, active: bool):
        self._active = active
        self._shadow.setEnabled(active)

        if active:
            self.setStyleSheet(
                f"GlowCard {{ background-color: #1A1D2B; border: 2px solid {self.accent_color}; "
                "border-radius: 8px; }}"
            )
            self.title_lbl.setStyleSheet(f"color: {self.accent_color};")
        else:
            self.setStyleSheet(
                "GlowCard { background-color: #14161F; border: 1px solid #222533; border-radius: 8px; } "
                "GlowCard:hover { background-color: #1C1F2E; border: 1px solid #33394D; }"
            )
            self.title_lbl.setStyleSheet("color: #FFFFFF;")

    def is_active(self) -> bool:
        return self._active

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
