"""
NUXARCHY Hardware Center: Optimizer > Quick Setup View
Features two side-by-side cards:
  - BOOSTER card with rocket vector icon, toggle switch, and CONFIGURE button
  - CLEANER card with vacuum vector icon, last cleaned stats, and SCAN NOW / SCHEDULER buttons
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QPainterPath

from nuxarchy.backend.capability import HardwareCapabilities


class RocketIconWidget(QWidget):
    """Vector outline rocket icon."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(80, 80)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        pen = QPen(QColor("#FFFFFF"), 2.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)

        # Fuselage
        body = QPainterPath()
        body.moveTo(40, 12)
        body.cubicTo(52, 24, 52, 44, 48, 54)
        body.lineTo(32, 54)
        body.cubicTo(28, 44, 28, 24, 40, 12)
        p.drawPath(body)

        # Porthole / window
        p.drawEllipse(36, 27, 8, 8)

        # Left wing
        left_fin = QPainterPath()
        left_fin.moveTo(29, 40)
        left_fin.cubicTo(20, 46, 18, 56, 18, 59)
        left_fin.lineTo(31, 55)
        p.drawPath(left_fin)

        # Right wing
        right_fin = QPainterPath()
        right_fin.moveTo(51, 40)
        right_fin.cubicTo(60, 46, 62, 56, 62, 59)
        right_fin.lineTo(49, 55)
        p.drawPath(right_fin)

        # Exhaust flames
        flame = QPainterPath()
        flame.moveTo(35, 57)
        flame.lineTo(40, 68)
        flame.lineTo(45, 57)
        p.drawPath(flame)


class VacuumIconWidget(QWidget):
    """Vector outline canister vacuum cleaner icon."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(80, 80)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        pen = QPen(QColor("#FFFFFF"), 2.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)

        # Canister body (rounded rectangle)
        p.drawRoundedRect(22, 28, 28, 30, 8, 8)

        # Large left wheel
        p.drawEllipse(18, 45, 14, 14)

        # Top handle
        handle = QPainterPath()
        handle.moveTo(31, 28)
        handle.lineTo(31, 22)
        handle.lineTo(41, 22)
        handle.lineTo(41, 28)
        p.drawPath(handle)

        # Hose extending from top-right of canister upwards and arching down
        hose = QPainterPath()
        hose.moveTo(43, 33)
        hose.cubicTo(56, 32, 60, 20, 56, 14)
        hose.cubicTo(52, 9, 42, 10, 45, 20)
        # Wand pipe down to floor
        hose.lineTo(60, 58)
        p.drawPath(hose)

        # Floor nozzle head
        nozzle = QPainterPath()
        nozzle.moveTo(54, 58)
        nozzle.lineTo(66, 58)
        p.drawPath(nozzle)


class ShieldCheckWidget(QWidget):
    """Green circle badge with white checkmark."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(20, 20)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # Green circle
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#00D26A"))
        p.drawEllipse(1, 1, 18, 18)

        # White checkmark
        pen = QPen(QColor("#FFFFFF"), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        check = QPainterPath()
        check.moveTo(6, 10)
        check.lineTo(9, 13)
        check.lineTo(14, 7)
        p.drawPath(check)


class ToggleSwitch(QWidget):
    """Custom toggle switch control with smooth indicator animation."""

    toggled = Signal(bool)

    def __init__(self, checked=True, parent=None):
        super().__init__(parent)
        self.setFixedSize(44, 24)
        self._checked = checked
        self.setCursor(Qt.PointingHandCursor)

    def is_checked(self):
        return self._checked

    def set_checked(self, val):
        self._checked = val
        self.update()

    def mousePressEvent(self, event):
        self._checked = not self._checked
        self.toggled.emit(self._checked)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        radius = h / 2.0

        if self._checked:
            # Track - blue (#0078D4)
            p.setBrush(QColor("#0078D4"))
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(0, 0, w, h, radius, radius)
            # Knob - white, on right
            knob_x = w - h + 3
            p.setBrush(QColor("#FFFFFF"))
            p.drawEllipse(int(knob_x), 3, h - 6, h - 6)
        else:
            # Track - dark gray
            p.setBrush(QColor("#374151"))
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(0, 0, w, h, radius, radius)
            # Knob - light gray, on left
            p.setBrush(QColor("#9CA3AF"))
            p.drawEllipse(3, 3, h - 6, h - 6)


class OptimizerQuickSetupView(QWidget):
    """Optimizer > Quick Setup tab content matching Screenshot 1."""

    request_tab_switch = Signal(int)

    def __init__(self, caps: HardwareCapabilities, parent=None):
        super().__init__(parent)
        self.caps = caps

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(40, 36, 40, 36)
        layout.setSpacing(28)

        # Two cards side by side
        cards_row = QHBoxLayout()
        cards_row.setSpacing(24)

        # =====================================================================
        # 1. BOOSTER CARD
        # =====================================================================
        booster_card = QFrame()
        booster_card.setStyleSheet("""
            QFrame {
                background-color: #171920;
                border: 1px solid #232734;
                border-radius: 8px;
            }
        """)
        booster_card.setMinimumHeight(440)
        booster_card.setMinimumWidth(380)

        b_layout = QVBoxLayout(booster_card)
        b_layout.setContentsMargins(36, 32, 36, 32)
        b_layout.setSpacing(18)

        b_title = QLabel("BOOSTER")
        b_title.setStyleSheet("color: #FFFFFF; font-size: 15px; font-weight: 800; letter-spacing: 1px; border: none; background: transparent;")
        b_layout.addWidget(b_title, alignment=Qt.AlignCenter)

        # Rocket vector icon
        rocket = RocketIconWidget()
        b_layout.addWidget(rocket, alignment=Qt.AlignCenter)

        # Description
        b_desc = QLabel("Run your games and apps faster with\nBOOSTER. Automatically boost all\nyour games.")
        b_desc.setAlignment(Qt.AlignCenter)
        b_desc.setWordWrap(True)
        b_desc.setStyleSheet("color: #9CA3AF; font-size: 12px; font-weight: 500; line-height: 1.5; border: none; background: transparent;")
        b_layout.addWidget(b_desc)

        b_layout.addSpacing(10)

        # Toggle row
        toggle_row = QHBoxLayout()
        toggle_row.setAlignment(Qt.AlignCenter)
        toggle_row.setSpacing(8)

        shield = ShieldCheckWidget()
        toggle_row.addWidget(shield)

        toggle_label = QLabel("Boost all my games")
        toggle_label.setStyleSheet("color: #FFFFFF; font-size: 12px; font-weight: 700; border: none; background: transparent;")
        toggle_row.addWidget(toggle_label)

        self.boost_toggle = ToggleSwitch(checked=True)
        toggle_row.addWidget(self.boost_toggle)

        self.lbl_on = QLabel("On")
        self.lbl_on.setStyleSheet("color: #9CA3AF; font-size: 12px; font-weight: 600; border: none; background: transparent;")
        toggle_row.addWidget(self.lbl_on)

        self.boost_toggle.toggled.connect(lambda chk: self.lbl_on.setText("On" if chk else "Off"))

        b_layout.addLayout(toggle_row)

        b_layout.addSpacing(12)

        # CONFIGURE button (Solid white button)
        btn_configure = QPushButton("CONFIGURE")
        btn_configure.setCursor(Qt.PointingHandCursor)
        btn_configure.setProperty("class", "whiteButton")
        btn_configure.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #000000;
                font-size: 11px;
                font-weight: 800;
                border-radius: 3px;
                padding: 8px 28px;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background-color: #E5E7EB;
            }
        """)
        btn_configure.clicked.connect(lambda: self.request_tab_switch.emit(1))
        b_layout.addWidget(btn_configure, alignment=Qt.AlignCenter)
        b_layout.addStretch()

        cards_row.addWidget(booster_card)

        # =====================================================================
        # 2. CLEANER CARD
        # =====================================================================
        cleaner_card = QFrame()
        cleaner_card.setStyleSheet("""
            QFrame {
                background-color: #171920;
                border: 1px solid #232734;
                border-radius: 8px;
            }
        """)
        cleaner_card.setMinimumHeight(440)
        cleaner_card.setMinimumWidth(380)

        c_layout = QVBoxLayout(cleaner_card)
        c_layout.setContentsMargins(36, 32, 36, 32)
        c_layout.setSpacing(18)

        c_title = QLabel("CLEANER")
        c_title.setStyleSheet("color: #FFFFFF; font-size: 15px; font-weight: 800; letter-spacing: 1px; border: none; background: transparent;")
        c_layout.addWidget(c_title, alignment=Qt.AlignCenter)

        # Vacuum vector icon
        vacuum = VacuumIconWidget()
        c_layout.addWidget(vacuum, alignment=Qt.AlignCenter)

        # Description
        c_desc = QLabel("Automatically clean and remove\nunnecessary files, free up and optimize\nstorage space.")
        c_desc.setAlignment(Qt.AlignCenter)
        c_desc.setWordWrap(True)
        c_desc.setStyleSheet("color: #9CA3AF; font-size: 12px; font-weight: 500; line-height: 1.5; border: none; background: transparent;")
        c_layout.addWidget(c_desc)

        c_layout.addSpacing(10)

        # Stats grid
        stats_row = QHBoxLayout()
        stats_row.setAlignment(Qt.AlignCenter)
        stats_row.setSpacing(40)

        # Left stat: Last cleaned
        col1 = QVBoxLayout()
        col1.setSpacing(3)
        lbl_lc_title = QLabel("Last cleaned:")
        lbl_lc_title.setStyleSheet("color: #FFFFFF; font-size: 11px; font-weight: 700; border: none; background: transparent;")
        lbl_lc_title.setAlignment(Qt.AlignCenter)
        col1.addWidget(lbl_lc_title)

        lbl_lc_val = QLabel("2/11/2026\n9:53:36 AM")
        lbl_lc_val.setStyleSheet("color: #9CA3AF; font-size: 10px; font-weight: 500; border: none; background: transparent;")
        lbl_lc_val.setAlignment(Qt.AlignCenter)
        col1.addWidget(lbl_lc_val)
        stats_row.addLayout(col1)

        # Right stat: Scheduled clean
        col2 = QVBoxLayout()
        col2.setSpacing(3)
        lbl_sc_title = QLabel("Scheduled clean:")
        lbl_sc_title.setStyleSheet("color: #FFFFFF; font-size: 11px; font-weight: 700; border: none; background: transparent;")
        lbl_sc_title.setAlignment(Qt.AlignCenter)
        col2.addWidget(lbl_sc_title)

        lbl_sc_val = QLabel("-")
        lbl_sc_val.setStyleSheet("color: #9CA3AF; font-size: 11px; font-weight: 500; border: none; background: transparent;")
        lbl_sc_val.setAlignment(Qt.AlignCenter)
        col2.addWidget(lbl_sc_val)
        stats_row.addLayout(col2)

        c_layout.addLayout(stats_row)

        c_layout.addSpacing(12)

        # Buttons row: SCAN NOW and SCHEDULER
        btns_row = QHBoxLayout()
        btns_row.setAlignment(Qt.AlignCenter)
        btns_row.setSpacing(14)

        btn_scan = QPushButton("SCAN NOW")
        btn_scan.setCursor(Qt.PointingHandCursor)
        btn_scan.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #000000;
                font-size: 11px;
                font-weight: 800;
                border-radius: 3px;
                padding: 8px 24px;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background-color: #E5E7EB;
            }
        """)
        btn_scan.clicked.connect(lambda: self.request_tab_switch.emit(2))
        btns_row.addWidget(btn_scan)

        btn_sched = QPushButton("SCHEDULER")
        btn_sched.setCursor(Qt.PointingHandCursor)
        btn_sched.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #000000;
                font-size: 11px;
                font-weight: 800;
                border-radius: 3px;
                padding: 8px 24px;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background-color: #E5E7EB;
            }
        """)
        btns_row.addWidget(btn_sched)

        c_layout.addLayout(btns_row)
        c_layout.addStretch()

        cards_row.addWidget(cleaner_card)

        layout.addLayout(cards_row)
        layout.addStretch()

        scroll.setWidget(container)
        main_box = QVBoxLayout(self)
        main_box.setContentsMargins(0, 0, 0, 0)
        main_box.addWidget(scroll)
