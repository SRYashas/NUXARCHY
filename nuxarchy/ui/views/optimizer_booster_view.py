"""
NUXARCHY Hardware Center: Optimizer > Booster View
Features:
  - Top category tabs with active white pill style: [ 🖥 (9/11) ] [ 🔄 (0/24) ] [ 🪟 (0/13) ] [ 🔲 (0/10) ]
  - Left panel: circular needle gauge (0%), "9 items to be optimized", "GO TO MY GAMES",
    "MANUAL BOOST" (white button), Memory Usage gradient bar with GB stats
  - Right panel: Optimization table with Checkbox, Name ▲, Description, Select all,
    and "RESET TO DEFAULT" white button
  - Bottom: Notification checkboxes
"""

import math
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QCheckBox, QProgressBar
)
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QBrush, QPainterPath

from nuxarchy.backend.capability import HardwareCapabilities


class BoosterGaugeWidget(QWidget):
    """Circular needle gauge showing optimization percentage (0-100%) matching Screenshot 2."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(190, 190)
        self._value = 0  # percentage

    def set_value(self, val: int):
        self._value = max(0, min(100, val))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2.0
        cy = h / 2.0
        radius = min(w, h) / 2.0 - 18

        arc_rect = QRectF(cx - radius, cy - radius, radius * 2, radius * 2)

        # Background track arc (dark slate/gray)
        bg_pen = QPen(QColor("#252A36"), 8, Qt.SolidLine, Qt.RoundCap)
        p.setPen(bg_pen)
        # Span: from 225 deg around clockwise 270 deg
        p.drawArc(arc_rect, 225 * 16, -270 * 16)

        # If value > 0, draw active gradient arc
        if self._value > 0:
            span = int(-270 * 16 * (self._value / 100.0))
            val_pen = QPen(QColor("#E51E43"), 8, Qt.SolidLine, Qt.RoundCap)
            p.setPen(val_pen)
            p.drawArc(arc_rect, 225 * 16, span)

        # Needle pointer from center towards arc
        # Angle at 0% is 225 deg (bottom-left)
        angle_deg = 225.0 - (270.0 * self._value / 100.0)
        angle_rad = math.radians(angle_deg)

        # Red center pivot circle
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#E51E43"))
        p.drawEllipse(int(cx - 7), int(cy - 7), 14, 14)

        # Needle line
        needle_len = radius - 10
        tip_x = cx + needle_len * math.cos(angle_rad)
        tip_y = cy - needle_len * math.sin(angle_rad)

        needle_pen = QPen(QColor("#E51E43"), 3.5, Qt.SolidLine, Qt.RoundCap)
        p.setPen(needle_pen)
        p.drawLine(int(cx), int(cy), int(tip_x), int(tip_y))

        # Center percentage text
        p.setPen(QColor("#FFFFFF"))
        font_pct = QFont("Segoe UI", 26, QFont.Bold)
        p.setFont(font_pct)
        # Center text inside arc
        p.drawText(arc_rect, Qt.AlignCenter, f"{self._value} %")


class MemoryBarWidget(QWidget):
    """Two-tone gradient memory bar (Used vs Free)."""

    def __init__(self, used_gb=9.5, total_gb=15.29, parent=None):
        super().__init__(parent)
        self.setFixedHeight(12)
        self.used_gb = used_gb
        self.total_gb = total_gb

    def set_stats(self, used_gb: float, total_gb: float):
        self.used_gb = used_gb
        self.total_gb = total_gb
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        used_ratio = min(1.0, max(0.0, self.used_gb / self.total_gb))
        used_w = int(w * used_ratio)

        from PySide6.QtGui import QLinearGradient
        # Used portion: pink to orange gradient
        grad = QLinearGradient(0, 0, used_w, 0)
        grad.setColorAt(0.0, QColor("#E02874"))
        grad.setColorAt(0.5, QColor("#FF4B26"))
        grad.setColorAt(1.0, QColor("#FF8A00"))

        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(grad))
        p.drawRoundedRect(0, 0, used_w, h, 2, 2)

        # Free portion: dark olive/slate
        p.setBrush(QColor("#4A4B42"))
        p.drawRoundedRect(used_w + 2, 0, max(0, w - used_w - 2), h, 2, 2)


class OptimizerBoosterView(QWidget):
    """Optimizer > Booster tab content matching Screenshot 2."""

    def __init__(self, caps: HardwareCapabilities, parent=None):
        super().__init__(parent)
        self.caps = caps

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(28, 20, 28, 20)
        main_layout.setSpacing(14)

        # ---------------------------------------------------------------------
        # TOP CATEGORY BAR (Matches Screenshot 2)
        # ---------------------------------------------------------------------
        cat_bar = QHBoxLayout()
        cat_bar.setSpacing(8)
        cat_bar.addStretch()

        import os
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "resources", "icons")
        self.cat_icon_data = [
            (os.path.join(icons_dir, "pc_icon_dark.svg"), os.path.join(icons_dir, "pc_icon_light.svg"), "(9/11)"),
            (os.path.join(icons_dir, "sync_icon_light.svg"), os.path.join(icons_dir, "sync_icon_light.svg"), "(0/24)"),
            (os.path.join(icons_dir, "windows_icon_light.svg"), os.path.join(icons_dir, "windows_icon_light.svg"), "(0/13)"),
            (os.path.join(icons_dir, "apps_icon_light.svg"), os.path.join(icons_dir, "apps_icon_light.svg"), "(0/10)"),
        ]

        from PySide6.QtGui import QIcon
        from PySide6.QtCore import QSize

        self.cat_buttons = []
        for i, (dark_icon, light_icon, count_str) in enumerate(self.cat_icon_data):
            btn = QPushButton(f" {count_str}")
            btn.setIcon(QIcon(dark_icon if i == 0 else light_icon))
            btn.setIconSize(QSize(18, 18))
            btn.setCursor(Qt.PointingHandCursor)
            if i == 0:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #FFFFFF;
                        color: #000000;
                        font-size: 11px;
                        font-weight: 800;
                        border: none;
                        border-radius: 2px;
                        padding: 6px 18px;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #14171E;
                        color: #8E95A5;
                        font-size: 11px;
                        font-weight: 700;
                        border: 1px solid #232734;
                        border-radius: 2px;
                        padding: 6px 18px;
                    }
                    QPushButton:hover {
                        color: #FFFFFF;
                        border-color: #383F52;
                    }
                """)
            btn.clicked.connect(lambda chk, idx=i: self._select_category_tab(idx))
            self.cat_buttons.append(btn)
            cat_bar.addWidget(btn)

        main_layout.addLayout(cat_bar)

        # Subtitle
        desc = QLabel("Essential items for CPU and memory optimization for overall performance boost.")
        desc.setStyleSheet("color: #8E95A5; font-size: 11px; font-weight: 500; margin-bottom: 4px;")
        main_layout.addWidget(desc)

        # ---------------------------------------------------------------------
        # MAIN SPLIT: LEFT PANEL + RIGHT TABLE
        # ---------------------------------------------------------------------
        split = QHBoxLayout()
        split.setSpacing(20)

        # === LEFT PANEL ===
        left_panel = QFrame()
        left_panel.setStyleSheet("""
            QFrame {
                background-color: #171920;
                border: 1px solid #232734;
                border-radius: 8px;
            }
        """)
        left_panel.setFixedWidth(290)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(22, 22, 22, 22)
        left_layout.setSpacing(14)

        # Title
        lbl_title = QLabel("BOOSTER")
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet("color: #FFFFFF; font-size: 15px; font-weight: 800; letter-spacing: 1px; border: none; background: transparent;")
        left_layout.addWidget(lbl_title)

        # Circular Gauge
        self.gauge = BoosterGaugeWidget()
        self.gauge.set_value(0)
        left_layout.addWidget(self.gauge, alignment=Qt.AlignCenter)

        # Items count (9 large white, items to be optimized gray)
        items_box = QVBoxLayout()
        items_box.setSpacing(2)
        lbl_num = QLabel("9")
        lbl_num.setAlignment(Qt.AlignCenter)
        lbl_num.setStyleSheet("color: #FFFFFF; font-size: 26px; font-weight: 800; border: none; background: transparent;")
        items_box.addWidget(lbl_num)

        lbl_sub = QLabel("items to be optimized")
        lbl_sub.setAlignment(Qt.AlignCenter)
        lbl_sub.setStyleSheet("color: #8E95A5; font-size: 11px; font-weight: 500; border: none; background: transparent;")
        items_box.addWidget(lbl_sub)
        left_layout.addLayout(items_box)

        left_layout.addSpacing(6)

        # Button 1: GO TO MY GAMES (Gradient)
        btn_games = QPushButton("GO TO MY GAMES")
        btn_games.setCursor(Qt.PointingHandCursor)
        btn_games.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #E02874, stop:0.5 #FF4B26, stop:1 #FF8A00);
                color: #FFFFFF;
                border: none;
                border-radius: 3px;
                padding: 9px 16px;
                font-size: 11px;
                font-weight: 800;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FF3385, stop:0.5 #FF5C38, stop:1 #FF9E1A);
            }
        """)
        left_layout.addWidget(btn_games)

        # Button 2: MANUAL BOOST (Solid white button)
        self.btn_manual = QPushButton("MANUAL BOOST")
        self.btn_manual.setCursor(Qt.PointingHandCursor)
        self.btn_manual.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #000000;
                border: none;
                border-radius: 3px;
                padding: 8px 16px;
                font-size: 11px;
                font-weight: 800;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background-color: #E5E7EB;
            }
        """)
        self.btn_manual.clicked.connect(self._toggle_boost)
        left_layout.addWidget(self.btn_manual)

        left_layout.addSpacing(8)

        # Memory Usage Section
        mem_title = QLabel("Memory Usage:")
        mem_title.setStyleSheet("color: #FFFFFF; font-size: 12px; font-weight: 700; border: none; background: transparent;")
        left_layout.addWidget(mem_title)

        self.mem_bar = MemoryBarWidget(used_gb=9.5, total_gb=15.29)
        left_layout.addWidget(self.mem_bar)

        # Memory stats row
        mem_stats = QHBoxLayout()
        mem_stats.setSpacing(6)
        self.lbl_total = QLabel("Total: 15.29 GB")
        self.lbl_total.setStyleSheet("color: #8E95A5; font-size: 10px; font-weight: 600; border: none; background: transparent;")
        mem_stats.addWidget(self.lbl_total)

        self.lbl_used = QLabel("Used: 9.5 GB")
        self.lbl_used.setStyleSheet("color: #8E95A5; font-size: 10px; font-weight: 600; border: none; background: transparent;")
        mem_stats.addWidget(self.lbl_used)

        self.lbl_free = QLabel("Free: 5.79 GB")
        self.lbl_free.setStyleSheet("color: #8E95A5; font-size: 10px; font-weight: 600; border: none; background: transparent;")
        mem_stats.addWidget(self.lbl_free)
        left_layout.addLayout(mem_stats)

        left_layout.addStretch()
        split.addWidget(left_panel)

        # === RIGHT PANEL: Optimization Table ===
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
        r_layout.setSpacing(10)

        # Table top toolbar
        top_row = QHBoxLayout()
        self.chk_select_all = QCheckBox("Select all")
        self.chk_select_all.setChecked(False)
        self.chk_select_all.setStyleSheet("color: #D1D5DB; font-size: 11px; font-weight: 700; border: none; background: transparent;")
        top_row.addWidget(self.chk_select_all)

        self.lbl_count = QLabel("9 out of 11 items selected")
        self.lbl_count.setStyleSheet("color: #8E95A5; font-size: 10px; font-weight: 500; border: none; background: transparent; margin-left: 20px;")
        top_row.addWidget(self.lbl_count)

        top_row.addStretch()
        r_layout.addLayout(top_row)

        # Optimization Table Items matching Screenshot 2
        self.opt_items = [
            ("Clear Clipboard", True, "Clear Clipboard history to release memory"),
            ("Disable automatic background recording", False, "Temporarily disables automatic background video recording when playing a game (DVR)"),
            ("Disable Automatic Updates", True, "Temporarily disable Windows automatic updates"),
            ("Disable CPU Core Parking", True, "Disables the CPU Core Parking mechanism to ensure all CPU cores remain active during game play."),
            ("Disable CPU Energy Efficiency", False, "Disables CPU Energy Efficiency features to ensure the CPU is always operating at high performance when gaming."),
            ("Disable File and Printer Sharing", True, "Temporarily disable File and Printer Sharing"),
            ("Disable Game Bar", True, "Temporarily disables the Microsoft Game Bar"),
            ("Disable Notifications", True, "Temporarily disables system notifications to reduce interruptions"),
            ("Disable Search Indexing", True, "Temporarily disables search indexing for improved disk performance"),
            ("Close Background Apps", True, "Closes non-essential background apps to free memory"),
            ("Set High Performance Power", True, "Switches to High Performance power plan"),
        ]

        self.table = QTableWidget(len(self.opt_items), 2)
        self.table.setHorizontalHeaderLabels(["Name ▲", "Description"])
        self.table.setColumnWidth(0, 320)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: transparent;
                border: none;
                color: #D1D5DB;
                font-size: 11px;
            }
            QTableWidget::item {
                padding: 10px 8px;
                border-bottom: 1px solid #1E222D;
            }
            QTableWidget::item:selected {
                background-color: #202430;
                color: #FFFFFF;
            }
            QHeaderView::section {
                background-color: #171920;
                color: #FFFFFF;
                font-size: 11px;
                font-weight: 700;
                padding: 8px 8px;
                border: none;
                border-bottom: 1px solid #232734;
            }
        """)

        self.check_boxes = []
        for row, (name, checked, desc_text) in enumerate(self.opt_items):
            # Checkbox + Name widget
            cell_w = QWidget()
            cell_l = QHBoxLayout(cell_w)
            cell_l.setContentsMargins(6, 0, 6, 0)
            cell_l.setSpacing(10)

            chk = QCheckBox(name)
            chk.setChecked(checked)
            chk.setStyleSheet("color: #E5E7EB; font-size: 11px; font-weight: 600; border: none; background: transparent;")
            chk.stateChanged.connect(self._on_item_toggled)
            self.check_boxes.append(chk)
            cell_l.addWidget(chk)
            self.table.setCellWidget(row, 0, cell_w)

            # Description item
            desc_item = QTableWidgetItem(desc_text)
            desc_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            desc_item.setForeground(QColor("#8E95A5"))
            self.table.setItem(row, 1, desc_item)

        r_layout.addWidget(self.table)

        # Bottom row with RESET TO DEFAULT button
        b_row = QHBoxLayout()
        b_row.addStretch()

        btn_reset = QPushButton("RESET TO DEFAULT")
        btn_reset.setCursor(Qt.PointingHandCursor)
        btn_reset.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #000000;
                border: none;
                border-radius: 3px;
                padding: 7px 22px;
                font-size: 11px;
                font-weight: 800;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background-color: #E5E7EB;
            }
        """)
        btn_reset.clicked.connect(self._reset_defaults)
        b_row.addWidget(btn_reset)
        r_layout.addLayout(b_row)

        split.addWidget(right_panel, 1)
        main_layout.addLayout(split)

        # ---------------------------------------------------------------------
        # BOTTOM NOTIFICATION CHECKBOXES (Matches Screenshot 2)
        # ---------------------------------------------------------------------
        bot_layout = QVBoxLayout()
        bot_layout.setSpacing(6)
        bot_layout.setContentsMargins(4, 4, 4, 4)

        self.chk_notify = QCheckBox("Notify me when boosting")
        self.chk_notify.setChecked(True)
        self.chk_notify.setStyleSheet("color: #D1D5DB; font-size: 11px; font-weight: 600; border: none; background: transparent;")
        bot_layout.addWidget(self.chk_notify)

        self.chk_auto_update = QCheckBox("Auto update Boost settings on profile change when Boost is active")
        self.chk_auto_update.setChecked(False)
        self.chk_auto_update.setStyleSheet("color: #8E95A5; font-size: 11px; font-weight: 500; border: none; background: transparent;")
        bot_layout.addWidget(self.chk_auto_update)

        main_layout.addLayout(bot_layout)
        main_layout.addStretch()

        scroll.setWidget(container)
        root_box = QVBoxLayout(self)
        root_box.setContentsMargins(0, 0, 0, 0)
        root_box.addWidget(scroll)

        self.chk_select_all.stateChanged.connect(self._on_select_all)

    def _select_category_tab(self, idx: int):
        from PySide6.QtGui import QIcon
        for i, btn in enumerate(self.cat_buttons):
            dark_icon, light_icon, count_str = self.cat_icon_data[i]
            if i == idx:
                btn.setIcon(QIcon(dark_icon))
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #FFFFFF;
                        color: #000000;
                        font-size: 11px;
                        font-weight: 800;
                        border: none;
                        border-radius: 2px;
                        padding: 6px 18px;
                    }
                """)
            else:
                btn.setIcon(QIcon(light_icon))
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #14171E;
                        color: #8E95A5;
                        font-size: 11px;
                        font-weight: 700;
                        border: 1px solid #232734;
                        border-radius: 2px;
                        padding: 6px 18px;
                    }
                    QPushButton:hover {
                        color: #FFFFFF;
                        border-color: #383F52;
                    }
                """)

    def _on_item_toggled(self):
        checked_count = sum(1 for chk in self.check_boxes if chk.isChecked())
        total = len(self.check_boxes)
        self.lbl_count.setText(f"{checked_count} out of {total} items selected")

    def _on_select_all(self, state):
        val = state.value if hasattr(state, "value") else state
        chk = bool(val == 2 or state == Qt.CheckState.Checked)
        for c in self.check_boxes:
            c.setChecked(chk)

    def _reset_defaults(self):
        defaults = [True, False, True, True, False, True, True, True, True, True, True]
        for c, d in zip(self.check_boxes, defaults):
            c.setChecked(d)

    def _toggle_boost(self):
        if self.gauge._value == 0:
            self.gauge.set_value(100)
            self.btn_manual.setText("RESTORE")
        else:
            self.gauge.set_value(0)
            self.btn_manual.setText("MANUAL BOOST")
