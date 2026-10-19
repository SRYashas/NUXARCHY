"""
NUXARCHY: System Vitals View
Matches the 4-card top row (GPU, CPU, RAM, STORAGE) and
3-card bottom row (YOUR SETTINGS, NETWORK, TOP PROCESSES).
"""

import os
import shutil
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame, QLabel,
    QGridLayout, QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from nuxarchy.ui.widgets.ring_gauge import NuxRingGaugeCard
from nuxarchy.backend.telemetry.system_monitor import SystemSnapshot
from nuxarchy.backend.capability import HardwareCapabilities


class DashboardView(QWidget):
    def __init__(self, caps: HardwareCapabilities, parent=None):
        super().__init__(parent)
        self.caps = caps

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 14, 20, 14)
        main_layout.setSpacing(12)

        # 1. Mode Sub-Bar & Temperature Unit Toggle
        sub_bar = QHBoxLayout()
        sub_bar.setContentsMargins(0, 0, 0, 0)

        lbl_mode = QLabel("Mode")
        lbl_mode.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: 700; margin-right: 8px;")
        sub_bar.addWidget(lbl_mode)

        # 3 mini mode icon buttons (Speedometer, Speedometer+Gear, Info)
        self.btn_icon1 = QPushButton("⚡")
        self.btn_icon1.setStyleSheet("background-color: #FFFFFF; color: #000; border-radius: 4px; padding: 4px 8px; font-weight: 900;")
        sub_bar.addWidget(self.btn_icon1)

        self.btn_icon2 = QPushButton("⚙")
        self.btn_icon2.setStyleSheet("background-color: #1A1D27; color: #FFF; border-radius: 4px; padding: 4px 8px;")
        sub_bar.addWidget(self.btn_icon2)

        self.btn_icon3 = QPushButton("ⓘ")
        self.btn_icon3.setStyleSheet("background-color: #1A1D27; color: #FFF; border-radius: 4px; padding: 4px 8px;")
        sub_bar.addWidget(self.btn_icon3)

        sub_bar.addStretch()

        lbl_temp_toggle = QLabel("Temperature  °F  [ ●  ]  °C  ⓘ")
        lbl_temp_toggle.setStyleSheet("color: #9CA3AF; font-size: 12px; font-weight: 600;")
        sub_bar.addWidget(lbl_temp_toggle)

        main_layout.addLayout(sub_bar)

        # Scroll Area for the two rows of cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        # --- ROW 1: GPU, CPU, RAM, STORAGE (4 Cards) ---
        row1 = QHBoxLayout()
        row1.setSpacing(12)

        # Card 1: GPU
        self.card_gpu = NuxRingGaugeCard("GPU", "GPU Utilization")
        row1.addWidget(self.card_gpu)

        # Card 2: CPU
        self.card_cpu = NuxRingGaugeCard("CPU", "CPU Utilization")
        row1.addWidget(self.card_cpu)

        # Card 3: RAM
        self.card_ram = NuxRingGaugeCard("RAM", "RAM Utilization")
        row1.addWidget(self.card_ram)

        # Card 4: STORAGE
        self.card_storage = self._build_storage_card()
        row1.addWidget(self.card_storage)

        layout.addLayout(row1)

        # --- ROW 2: YOUR SETTINGS, NETWORK, TOP PROCESSES (3 Cards) ---
        row2 = QHBoxLayout()
        row2.setSpacing(12)

        # Card 5: YOUR SETTINGS
        self.card_settings = self._build_your_settings_card()
        row2.addWidget(self.card_settings, 1)

        # Card 6: NETWORK
        self.card_network = self._build_network_card()
        row2.addWidget(self.card_network, 1)

        # Card 7: TOP PROCESSES
        self.card_processes = self._build_processes_card()
        row2.addWidget(self.card_processes, 2)

        layout.addLayout(row2)
        layout.addStretch()

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def _build_storage_card(self) -> QFrame:
        card = QFrame()
        card.setProperty("class", "nuxarchyCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(14)

        title = QLabel("STORAGE")
        title.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: 800; letter-spacing: 0.5px;")
        layout.addWidget(title)

        # Drive 1 (C:\ or /)
        d1_row = QVBoxLayout()
        d1_row.setSpacing(4)
        lbl1 = QLabel("Root / C:\\")
        lbl1.setStyleSheet("color: #9CA3AF; font-size: 11px; font-weight: 700;")
        d1_row.addWidget(lbl1)

        self.bar_drive1 = QProgressBar()
        self.bar_drive1.setStyleSheet("""
            QProgressBar {
                background-color: #1F232E;
                height: 12px;
                border-radius: 6px;
                border: none;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FF2A54, stop:0.6 #FF7A00, stop:1 #FFD000);
                border-radius: 6px;
            }
        """)
        d1_row.addWidget(self.bar_drive1)

        self.lbl_drive1_text = QLabel("90.0 GB free of 366.3 GB")
        self.lbl_drive1_text.setStyleSheet("color: #D1D5DB; font-size: 11px; font-weight: 600;")
        d1_row.addWidget(self.lbl_drive1_text)
        layout.addLayout(d1_row)

        # Drive 2 (D:\ or /home)
        d2_row = QVBoxLayout()
        d2_row.setSpacing(4)
        lbl2 = QLabel("Data / D:\\")
        lbl2.setStyleSheet("color: #9CA3AF; font-size: 11px; font-weight: 700;")
        d2_row.addWidget(lbl2)

        self.bar_drive2 = QProgressBar()
        self.bar_drive2.setStyleSheet("""
            QProgressBar {
                background-color: #1F232E;
                height: 12px;
                border-radius: 6px;
                border: none;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FF2A54, stop:0.6 #FF7A00, stop:1 #FFD000);
                border-radius: 6px;
            }
        """)
        d2_row.addWidget(self.bar_drive2)

        self.lbl_drive2_text = QLabel("214.4 GB free of 585.9 GB")
        self.lbl_drive2_text.setStyleSheet("color: #D1D5DB; font-size: 11px; font-weight: 600;")
        d2_row.addWidget(self.lbl_drive2_text)
        layout.addLayout(d2_row)

        self._update_storage_stats()
        layout.addStretch()
        return card

    def _update_storage_stats(self):
        try:
            # Query drive 1
            root_path = "C:\\" if os.name == "nt" else "/"
            total, used, free = shutil.disk_usage(root_path)
            pct = int((used / total) * 100)
            self.bar_drive1.setValue(pct)
            self.lbl_drive1_text.setText(f"{free / (1024**3):.1f} GB free of {total / (1024**3):.1f} GB")

            # Query drive 2 if exists
            d2_path = "D:\\" if os.name == "nt" and os.path.exists("D:\\") else "/home"
            if os.path.exists(d2_path):
                t2, u2, f2 = shutil.disk_usage(d2_path)
                pct2 = int((u2 / t2) * 100)
                self.bar_drive2.setValue(pct2)
                self.lbl_drive2_text.setText(f"{f2 / (1024**3):.1f} GB free of {t2 / (1024**3):.1f} GB")
        except Exception:
            pass

    def _build_your_settings_card(self) -> QFrame:
        card = QFrame()
        card.setProperty("class", "nuxarchyCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        title = QLabel("YOUR SETTINGS")
        title.setStyleSheet("color: #FFFFFF; font-size: 15px; font-weight: 800; letter-spacing: 0.5px;")
        layout.addWidget(title)

        lbl_sub = QLabel("Performance Control")
        lbl_sub.setStyleSheet("color: #9CA3AF; font-size: 11px; font-weight: 600;")
        layout.addWidget(lbl_sub)

        # Glowing gradient border button
        btn_perf = QPushButton("PERFORMANCE")
        btn_perf.setStyleSheet("""
            QPushButton {
                background-color: #12141A;
                color: #FFFFFF;
                font-weight: 800;
                font-size: 12px;
                letter-spacing: 1px;
                border: 2px solid #FF8C00;
                border-radius: 4px;
                padding: 8px 14px;
            }
        """)
        layout.addWidget(btn_perf)
        layout.addStretch()
        return card

    def _build_network_card(self) -> QFrame:
        card = QFrame()
        card.setProperty("class", "nuxarchyCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        title = QLabel("NETWORK")
        title.setStyleSheet("color: #FFFFFF; font-size: 15px; font-weight: 800; letter-spacing: 0.5px;")
        layout.addWidget(title)

        # Digital Upload & Download Readouts
        r1 = QHBoxLayout()
        self.val_up = QLabel("0.0")
        self.val_up.setStyleSheet("color: #FFFFFF; font-size: 26px; font-weight: 800;")
        r1.addWidget(self.val_up)
        lbl_up = QLabel("Upload Speed\nMbps")
        lbl_up.setStyleSheet("color: #9CA3AF; font-size: 10px; font-weight: 700;")
        r1.addWidget(lbl_up)
        r1.addStretch()
        layout.addLayout(r1)

        r2 = QHBoxLayout()
        self.val_down = QLabel("0.0")
        self.val_down.setStyleSheet("color: #FFFFFF; font-size: 26px; font-weight: 800;")
        r2.addWidget(self.val_down)
        lbl_down = QLabel("Download Speed\nMbps")
        lbl_down.setStyleSheet("color: #9CA3AF; font-size: 10px; font-weight: 700;")
        r2.addWidget(lbl_down)
        r2.addStretch()
        layout.addLayout(r2)

        lbl_nb = QLabel("Network Booster")
        lbl_nb.setStyleSheet("color: #9CA3AF; font-size: 11px; font-weight: 600; margin-top: 4px;")
        layout.addWidget(lbl_nb)

        btn_cust = QPushButton("CUSTOM")
        btn_cust.setStyleSheet("""
            QPushButton {
                background-color: #12141A;
                color: #FFFFFF;
                font-weight: 800;
                font-size: 12px;
                letter-spacing: 1px;
                border: 2px solid #FF8C00;
                border-radius: 4px;
                padding: 6px 14px;
            }
        """)
        layout.addWidget(btn_cust)
        layout.addStretch()
        return card

    def _build_processes_card(self) -> QFrame:
        card = QFrame()
        card.setProperty("class", "nuxarchyCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        title = QLabel("TOP PROCESSES")
        title.setStyleSheet("color: #FFFFFF; font-size: 15px; font-weight: 800; letter-spacing: 0.5px;")
        layout.addWidget(title)

        # Table matching Screenshot 2
        self.table = QTableWidget(5, 5)
        self.table.setHorizontalHeaderLabels(["NAME", "CPU", "GPU", "RAM", "ACTION"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: transparent;
                border: none;
                color: #E5E7EB;
                font-size: 11px;
            }
            QHeaderView::section {
                background-color: transparent;
                color: #9CA3AF;
                font-weight: 800;
                font-size: 10px;
                border: none;
                padding-bottom: 6px;
            }
        """)

        # Populate top processes
        procs = [
            ("Python", "1%", "0%", "161MB"),
            ("Antigravity IDE", "1%", "0%", "1173MB"),
            ("Microsoft Cross Device", "1%", "0%", "60MB"),
            ("brave", "0%", "0%", "450MB"),
            ("System", "0%", "0%", "80MB")
        ]
        for row, (p_name, cpu, gpu, ram) in enumerate(procs):
            self.table.setItem(row, 0, QTableWidgetItem(f"🐍  {p_name}"))
            self.table.setItem(row, 1, QTableWidgetItem(cpu))
            self.table.setItem(row, 2, QTableWidgetItem(gpu))
            self.table.setItem(row, 3, QTableWidgetItem(ram))
            self.table.setItem(row, 4, QTableWidgetItem("🚫"))

        layout.addWidget(self.table)

        # Bottom link
        link = QLabel("<a href='#' style='color:#9CA3AF; text-decoration:underline;'>Open Task Manager</a>")
        link.setAlignment(Qt.AlignRight)
        layout.addWidget(link)
        return card

    def update_telemetry(self, snap: SystemSnapshot):
        # 1. Update GPU Card (matches Screenshot 2: 0% GPU Utilization, 55°C GPU Temperature)
        self.card_gpu.set_data(
            val=snap.gpu_nvidia.utilization_gpu_percent,
            temp_c=snap.gpu_nvidia.temperature_celsius,
            temp_label="GPU Temperature"
        )

        # 2. Update CPU Card (matches Screenshot 2: 18% CPU Utilization, 85°C CPU Temperature)
        self.card_cpu.set_data(
            val=snap.cpu.total_utilization,
            temp_c=snap.cpu.temperature_celsius,
            temp_label="CPU Temperature"
        )

        # 3. Update RAM Card (matches Screenshot 2: 61% RAM Utilization, 9.4GB / 15.3GB)
        used_gb = snap.memory.used_ram_mb / 1024.0
        tot_gb = snap.memory.total_ram_mb / 1024.0
        self.card_ram.set_data(
            val=snap.memory.ram_utilization_percent,
            bottom_detail=f"{used_gb:.1f}GB / {tot_gb:.1f}GB"
        )

        # 4. Update Network Mbps
        up_mbps = (snap.network.upload_kbps * 8) / 1024.0
        down_mbps = (snap.network.download_kbps * 8) / 1024.0
        self.val_up.setText(f"{up_mbps:.1f}")
        self.val_down.setText(f"{down_mbps:.1f}")
