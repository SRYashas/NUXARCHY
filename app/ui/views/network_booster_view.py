"""
OMEN Gaming Hub: Network Booster View (Pixel-Perfect Recreation)
Matches Screenshot 5:
Mode [OFF | AUTO | CUSTOM], Total Bandwidth Usage circular ring with 0.00 Mbps,
and application priority/blocking table.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QCheckBox
)
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QFont
from PySide6.QtCore import Qt, QRectF

from backend.capability import HardwareCapabilities
from backend.telemetry.system_monitor import SystemSnapshot


class NetworkRingWidget(QWidget):
    """Large circular bandwidth ring matching Screenshot 5."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(280, 260)
        self.bandwidth_mbps = 0.00

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        size = min(w, h) - 40
        rect = QRectF((w - size) / 2.0, (h - size) / 2.0 - 10, size, size)

        # Thin Red/Orange Ring Stroke
        ring_pen = QPen(QColor("#E51E43"), 3.5)
        painter.setPen(ring_pen)
        painter.drawEllipse(rect)

        # Central text: "0.00" and "Mbps"
        painter.setPen(QColor(255, 255, 255))
        font_num = QFont("Segoe UI", 32, QFont.Bold)
        painter.setFont(font_num)
        painter.drawText(QRectF(0, h / 2.0 - 40, w, 45), Qt.AlignCenter, f"{self.bandwidth_mbps:.2f}")

        painter.setPen(QColor(156, 163, 175))
        font_sub = QFont("Segoe UI", 12, QFont.Bold)
        painter.setFont(font_sub)
        painter.drawText(QRectF(0, h / 2.0 + 8, w, 24), Qt.AlignCenter, "Mbps")


class NetworkBoosterView(QWidget):
    def __init__(self, caps: HardwareCapabilities, parent=None):
        super().__init__(parent)
        self.caps = caps

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(14)

        # 1. Top Sub-Bar: Mode [ OFF | AUTO | CUSTOM ], description, search, and Dual Force
        top_bar = QHBoxLayout()
        top_bar.setSpacing(12)

        lbl_m = QLabel("Mode")
        lbl_m.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: 700;")
        top_bar.addWidget(lbl_m)

        # Segmented mode buttons
        mode_box = QFrame()
        mode_box.setStyleSheet("background-color: #12141A; border: 1px solid #1E222D; border-radius: 4px;")
        m_layout = QHBoxLayout(mode_box)
        m_layout.setContentsMargins(2, 2, 2, 2)
        m_layout.setSpacing(2)

        self.btn_off = QPushButton("OFF")
        self.btn_off.setStyleSheet("background: transparent; color: #9CA3AF; font-size: 11px; font-weight: 700; padding: 5px 12px; border: none;")
        m_layout.addWidget(self.btn_off)

        self.btn_auto = QPushButton("AUTO")
        self.btn_auto.setStyleSheet("background: transparent; color: #9CA3AF; font-size: 11px; font-weight: 700; padding: 5px 12px; border: none;")
        m_layout.addWidget(self.btn_auto)

        self.btn_custom = QPushButton("CUSTOM")
        self.btn_custom.setStyleSheet("background: #FFFFFF; color: #000000; font-size: 11px; font-weight: 800; padding: 5px 14px; border-radius: 3px; border: none;")
        m_layout.addWidget(self.btn_custom)
        top_bar.addWidget(mode_box)

        lbl_desc = QLabel("Adjust the priority levels of each app manually below, or block apps from accessing network. All apps will default to MEDIUM.")
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("color: #6B7280; font-size: 11px; margin-left: 10px;")
        top_bar.addWidget(lbl_desc, 1)

        # Search box
        search = QLineEdit()
        search.setPlaceholderText("Search 🔍")
        search.setStyleSheet("background-color: #12141A; color: #FFF; border: 1px solid #232734; border-radius: 4px; padding: 5px 10px; font-size: 11px; max-width: 140px;")
        top_bar.addWidget(search)

        # Dual Force toggle
        lbl_df = QLabel("Dual Force ⓘ  OFF [ ● ] ON ⚠️")
        lbl_df.setStyleSheet("color: #9CA3AF; font-size: 11px; font-weight: 600;")
        top_bar.addWidget(lbl_df)

        layout.addLayout(top_bar)

        # 2. Main Content Split: Left (Ring) + Right (App Table)
        main_split = QHBoxLayout()
        main_split.setSpacing(20)

        # Left Column: Total Bandwidth Usage Ring
        left_col = QVBoxLayout()
        left_col.setAlignment(Qt.AlignTop)

        lbl_ring_title = QLabel("Total Bandwidth Usage")
        lbl_ring_title.setAlignment(Qt.AlignCenter)
        lbl_ring_title.setStyleSheet("color: #FFFFFF; font-size: 15px; font-weight: 800;")
        left_col.addWidget(lbl_ring_title)

        self.ring = NetworkRingWidget()
        left_col.addWidget(self.ring, alignment=Qt.AlignCenter)

        # Legend: ■ 100% ◆ HP Omen CommandCenter
        legend = QLabel("<span style='color:#E51E43'>■ 100%</span>   <span style='color:#FF2A54'>◆</span> HP Omen CommandCenter")
        legend.setAlignment(Qt.AlignCenter)
        legend.setStyleSheet("color: #D1D5DB; font-size: 12px; font-weight: 700;")
        left_col.addWidget(legend)

        main_split.addLayout(left_col, 1)

        # Right Column: Apps Process Priority & Blocking Table
        right_card = QFrame()
        right_card.setProperty("class", "omenCard")
        r_layout = QVBoxLayout(right_card)
        r_layout.setContentsMargins(8, 8, 8, 8)

        self.table = QTableWidget(12, 5)
        self.table.setHorizontalHeaderLabels(["App Name", "Download", "Upload", "Priority", "Block"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: transparent;
                border: none;
                color: #FFFFFF;
                font-size: 12px;
            }
            QHeaderView::section {
                background-color: transparent;
                color: #9CA3AF;
                font-weight: 800;
                font-size: 11px;
                border: none;
                padding-bottom: 8px;
            }
        """)

        apps_data = [
            ("Antigravity IDE", "0 kbps", "0 kbps"),
            ("brave", "0 kbps", "0 kbps"),
            ("ChatGPT Classic", "0 kbps", "0 kbps"),
            ("CrossDeviceService", "0 kbps", "0 kbps"),
            ("HP Omen CommandCenter", "0 kbps", "1 kbps"),
            ("kilo", "0 kbps", "0 kbps"),
            ("language_server_linux_x64", "0 kbps", "0 kbps"),
            ("nvcontainer", "0 kbps", "0 kbps"),
            ("python", "0 kbps", "0 kbps"),
            ("SearchHost", "0 kbps", "0 kbps"),
            ("services", "0 kbps", "0 kbps"),
            ("wininit", "0 kbps", "0 kbps"),
        ]

        for row, (name, down, up) in enumerate(apps_data):
            self.table.setItem(row, 0, QTableWidgetItem(f"🔹  {name}"))
            self.table.setItem(row, 1, QTableWidgetItem(down))
            self.table.setItem(row, 2, QTableWidgetItem(up))

            # Priority dropdown
            combo = QComboBox()
            combo.addItems(["HIGH", "MEDIUM", "LOW"])
            combo.setCurrentText("MEDIUM")
            combo.setStyleSheet("""
                QComboBox {
                    background-color: #12141A;
                    color: #E51E43;
                    border: 1px solid #282D3D;
                    border-radius: 4px;
                    padding: 3px 8px;
                    font-size: 10px;
                    font-weight: 800;
                }
            """)
            self.table.setCellWidget(row, 3, combo)

            # Block switch / checkbox
            chk = QCheckBox()
            chk.setStyleSheet("margin-left: 10px;")
            self.table.setCellWidget(row, 4, chk)

        r_layout.addWidget(self.table)
        main_split.addWidget(right_card, 2)

        layout.addLayout(main_split)

    def update_telemetry(self, snap: SystemSnapshot):
        total_mbps = ((snap.network.download_kbps + snap.network.upload_kbps) * 8) / 1024.0
        self.ring.bandwidth_mbps = total_mbps
        self.ring.update()
