"""
OMEN Gaming Hub: HOME View (Pixel-Perfect Recreation)
Matches Screenshot 1:
MY GEAR (1) with OMEN 16 and accessories cards,
and WIDGETS (7) with MY PC (3 mini rings), OMEN AI, RECENT GAMES, TOP DEALS, BOOSTER, and FAVORITE GAMES.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame, QLabel,
    QPushButton, QGridLayout, QCheckBox
)
from PySide6.QtCore import Qt

from nuxarchy.backend.capability import HardwareCapabilities
from nuxarchy.backend.telemetry.system_monitor import SystemSnapshot


class HomeView(QWidget):
    def __init__(self, caps: HardwareCapabilities, on_device_click=None, parent=None):
        super().__init__(parent)
        self.caps = caps
        self.on_device_click = on_device_click

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 16, 24, 20)
        layout.setSpacing(18)

        # 1. Section: MY GEAR (1)
        sec_gear = QLabel("▼  MY GEAR (1)")
        sec_gear.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: 800; letter-spacing: 0.5px;")
        layout.addWidget(sec_gear)

        gear_row = QHBoxLayout()
        gear_row.setSpacing(14)

        # Card 1: OMEN 16
        self.card_omen = QFrame()
        self.card_omen.setFixedSize(220, 140)
        self.card_omen.setProperty("class", "omenCard")
        self.card_omen.setCursor(Qt.PointingHandCursor)
        o_layout = QVBoxLayout(self.card_omen)
        o_layout.setContentsMargins(12, 10, 12, 10)

        top_dots = QLabel("•••")
        top_dots.setStyleSheet("color: #6B7280; font-size: 11px;")
        o_layout.addWidget(top_dots)

        laptop_img = QLabel("💻")
        laptop_img.setAlignment(Qt.AlignCenter)
        laptop_img.setStyleSheet("font-size: 42px;")
        o_layout.addWidget(laptop_img)

        lbl_dev_name = QLabel("OMEN 16")
        lbl_dev_name.setAlignment(Qt.AlignCenter)
        lbl_dev_name.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: 800;")
        o_layout.addWidget(lbl_dev_name)

        if on_device_click:
            self.card_omen.mousePressEvent = lambda e: on_device_click()

        gear_row.addWidget(self.card_omen)

        # Card 2: Add Gear
        card_add = QFrame()
        card_add.setFixedSize(220, 140)
        card_add.setProperty("class", "omenCard")
        a_layout = QVBoxLayout(card_add)
        a_layout.setAlignment(Qt.AlignCenter)
        a_layout.setSpacing(6)

        plug_icon = QLabel("◇")
        plug_icon.setAlignment(Qt.AlignCenter)
        plug_icon.setStyleSheet("color: #9CA3AF; font-size: 24px;")
        a_layout.addWidget(plug_icon)

        add_msg = QLabel("Your OMEN 16 is looking a little lonely.\nLet's fix that. Check out OMEN.com")
        add_msg.setAlignment(Qt.AlignCenter)
        add_msg.setWordWrap(True)
        add_msg.setStyleSheet("color: #9CA3AF; font-size: 10px; font-weight: 600; line-height: 1.3;")
        a_layout.addWidget(add_msg)

        gear_row.addWidget(card_add)
        gear_row.addStretch()
        layout.addLayout(gear_row)

        # 2. Section: WIDGETS (7)
        sec_widgets = QLabel("▼  WIDGETS (7)")
        sec_widgets.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: 800; letter-spacing: 0.5px; margin-top: 6px;")
        layout.addWidget(sec_widgets)

        grid = QGridLayout()
        grid.setSpacing(14)

        # Widget 1: MY PC (3 mini rings)
        self.card_my_pc = self._build_my_pc_widget()
        grid.addWidget(self.card_my_pc, 0, 0)

        # Widget 2: OMEN AI BETA
        card_ai = self._build_omen_ai_widget()
        grid.addWidget(card_ai, 0, 1)

        # Widget 3: RECENT GAMES
        card_recents = self._build_recent_games_widget()
        grid.addWidget(card_recents, 0, 2)

        # Widget 4: TOP DEALS
        card_deals = self._build_top_deals_widget()
        grid.addWidget(card_deals, 1, 0)

        # Widget 5: GALLERY
        card_gallery = self._build_gallery_widget()
        grid.addWidget(card_gallery, 1, 1)

        # Widget 6: BOOSTER
        card_booster = self._build_booster_widget()
        grid.addWidget(card_booster, 1, 2)

        layout.addLayout(grid)

        # Widget 7: FAVORITE GAMES (full width bar)
        card_fav = self._build_favorite_games_widget()
        layout.addWidget(card_fav)

        layout.addStretch()
        scroll.setWidget(container)

        main_box = QVBoxLayout(self)
        main_box.setContentsMargins(0, 0, 0, 0)
        main_box.addWidget(scroll)

    def _build_my_pc_widget(self) -> QFrame:
        card = QFrame()
        card.setProperty("class", "omenCard")
        card.setMinimumHeight(170)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        lbl = QLabel("MY PC")
        lbl.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: 800;")
        layout.addWidget(lbl)

        rings_row = QHBoxLayout()
        rings_row.setSpacing(10)

        # Mini ring 1: CPU
        self.val_home_cpu = QLabel("18%")
        self.val_home_cpu.setStyleSheet("color: #FFFFFF; font-size: 18px; font-weight: 800; border: 3px solid #E024C3; border-radius: 28px; padding: 12px 6px;")
        self.val_home_cpu.setAlignment(Qt.AlignCenter)
        c1 = QVBoxLayout()
        c1.addWidget(QLabel("CPU", alignment=Qt.AlignCenter))
        c1.addWidget(self.val_home_cpu)
        self.lbl_home_cpu_temp = QLabel("85°C", alignment=Qt.AlignCenter)
        self.lbl_home_cpu_temp.setStyleSheet("color: #00FF85; font-size: 11px; font-weight: 800;")
        c1.addWidget(self.lbl_home_cpu_temp)
        rings_row.addLayout(c1)

        # Mini ring 2: GPU
        self.val_home_gpu = QLabel("0%")
        self.val_home_gpu.setStyleSheet("color: #FFFFFF; font-size: 18px; font-weight: 800; border: 3px solid #E024C3; border-radius: 28px; padding: 12px 6px;")
        self.val_home_gpu.setAlignment(Qt.AlignCenter)
        c2 = QVBoxLayout()
        c2.addWidget(QLabel("GPU", alignment=Qt.AlignCenter))
        c2.addWidget(self.val_home_gpu)
        self.lbl_home_gpu_temp = QLabel("55°C", alignment=Qt.AlignCenter)
        self.lbl_home_gpu_temp.setStyleSheet("color: #00FF85; font-size: 11px; font-weight: 800;")
        c2.addWidget(self.lbl_home_gpu_temp)
        rings_row.addLayout(c2)

        # Mini ring 3: RAM
        self.val_home_ram = QLabel("61%")
        self.val_home_ram.setStyleSheet("color: #FFFFFF; font-size: 18px; font-weight: 800; border: 3px solid #E024C3; border-radius: 28px; padding: 12px 6px;")
        self.val_home_ram.setAlignment(Qt.AlignCenter)
        c3 = QVBoxLayout()
        c3.addWidget(QLabel("RAM", alignment=Qt.AlignCenter))
        c3.addWidget(self.val_home_ram)
        self.lbl_home_ram_stat = QLabel("9.4GB / 15GB", alignment=Qt.AlignCenter)
        self.lbl_home_ram_stat.setStyleSheet("color: #00FF85; font-size: 10px; font-weight: 800;")
        c3.addWidget(self.lbl_home_ram_stat)
        rings_row.addLayout(c3)

        layout.addLayout(rings_row)
        return card

    def _build_omen_ai_widget(self) -> QFrame:
        card = QFrame()
        card.setProperty("class", "omenCard")
        card.setMinimumHeight(170)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)

        lbl = QLabel("OMEN AI <span style='color:#FF9E00; font-size:10px;'>BETA</span>")
        lbl.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: 800;")
        layout.addWidget(lbl)

        row = QHBoxLayout()
        text_col = QVBoxLayout()
        t = QLabel("YOU'RE MAXIMIZING\nPERFORMANCE WITH\nOMEN AI")
        t.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: 900; line-height: 1.2;")
        text_col.addWidget(t)

        btn_cfg = QPushButton("CONFIGURE")
        btn_cfg.setStyleSheet("background-color: transparent; border: 1px solid #4B5563; border-radius: 4px; color: #FFF; font-size: 10px; font-weight: 800; padding: 4px 10px; max-width: 90px;")
        text_col.addWidget(btn_cfg)
        row.addLayout(text_col)

        diamond = QLabel("◆")
        diamond.setStyleSheet("color: #FF5400; font-size: 54px;")
        diamond.setAlignment(Qt.AlignCenter)
        row.addWidget(diamond)

        layout.addLayout(row)
        return card

    def _build_recent_games_widget(self) -> QFrame:
        card = QFrame()
        card.setProperty("class", "omenCard")
        card.setMinimumHeight(170)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)

        lbl = QLabel("RECENT GAMES")
        lbl.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: 800;")
        layout.addWidget(lbl)

        games_row = QHBoxLayout()
        for g_name, icon in [("Counter-Strike 2", "🎮"), ("Cyberpunk 2077", "🌆"), ("Steam Games", "🕹️")]:
            tile = QFrame()
            tile.setStyleSheet("background-color: #1A1D27; border-radius: 6px; padding: 10px;")
            tl = QVBoxLayout(tile)
            tl.setAlignment(Qt.AlignCenter)
            ic = QLabel(icon, alignment=Qt.AlignCenter)
            ic.setStyleSheet("font-size: 26px;")
            tl.addWidget(ic)
            nm = QLabel(g_name, alignment=Qt.AlignCenter)
            nm.setWordWrap(True)
            nm.setStyleSheet("color: #FFF; font-size: 10px; font-weight: 700;")
            tl.addWidget(nm)
            games_row.addWidget(tile)

        layout.addLayout(games_row)
        return card

    def _build_top_deals_widget(self) -> QFrame:
        card = QFrame()
        card.setProperty("class", "omenCard")
        card.setMinimumHeight(140)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)

        lbl = QLabel("TOP DEALS")
        lbl.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: 800;")
        layout.addWidget(lbl)

        banner = QLabel("CONTROL RESONANT\nSpecial Edition • Available on Steam")
        banner.setAlignment(Qt.AlignCenter)
        banner.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1F2937, stop:1 #374151);
            color: #FFFFFF;
            font-size: 12px;
            font-weight: 800;
            border-radius: 6px;
            padding: 18px;
        """)
        layout.addWidget(banner)
        return card

    def _build_gallery_widget(self) -> QFrame:
        card = QFrame()
        card.setProperty("class", "omenCard")
        card.setMinimumHeight(140)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)

        lbl = QLabel("GALLERY")
        lbl.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: 800;")
        layout.addWidget(lbl)

        box = QHBoxLayout()
        icon = QLabel("🔧")
        icon.setStyleSheet("font-size: 28px;")
        box.addWidget(icon)

        txt = QVBoxLayout()
        t = QLabel("Local Game Wallpapers & Screenshots")
        t.setStyleSheet("color: #9CA3AF; font-size: 11px;")
        txt.addWidget(t)

        btn = QPushButton("VIEW GALLERY")
        btn.setStyleSheet("background: transparent; color: #00FFD1; border: 1px solid #00FFD1; border-radius: 4px; padding: 4px 10px; font-size: 10px; font-weight: 800; max-width: 110px;")
        txt.addWidget(btn)
        box.addLayout(txt)

        layout.addLayout(box)
        return card

    def _build_booster_widget(self) -> QFrame:
        card = QFrame()
        card.setProperty("class", "omenCard")
        card.setMinimumHeight(140)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        lbl = QLabel("BOOSTER")
        lbl.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: 800;")
        layout.addWidget(lbl)

        r = QHBoxLayout()
        chk = QCheckBox("Boost all my games")
        chk.setChecked(True)
        chk.setStyleSheet("color: #FFFFFF; font-weight: 700; font-size: 12px;")
        r.addWidget(chk)
        layout.addLayout(r)

        btn = QPushButton("CONFIGURE")
        btn.setStyleSheet("background-color: transparent; border: 1px solid #4B5563; border-radius: 4px; color: #FFF; font-size: 10px; font-weight: 800; padding: 4px 12px; max-width: 100px;")
        layout.addWidget(btn)
        return card

    def _build_favorite_games_widget(self) -> QFrame:
        card = QFrame()
        card.setProperty("class", "omenCard")
        card.setMinimumHeight(110)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setAlignment(Qt.AlignCenter)

        t = QLabel("FAVORITE GAMES")
        t.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: 800;")
        layout.addWidget(t)

        icon = QLabel("🎮", alignment=Qt.AlignCenter)
        icon.setStyleSheet("font-size: 32px;")
        layout.addWidget(icon)

        sub = QLabel("Set up your favorite games", alignment=Qt.AlignCenter)
        sub.setStyleSheet("color: #9CA3AF; font-size: 12px; font-weight: 700;")
        layout.addWidget(sub)
        return card

    def update_telemetry(self, snap: SystemSnapshot):
        self.val_home_cpu.setText(f"{snap.cpu.total_utilization:.0f}%")
        self.val_home_gpu.setText(f"{snap.gpu_nvidia.utilization_gpu_percent:.0f}%")
        self.val_home_ram.setText(f"{snap.memory.ram_utilization_percent:.0f}%")
        if snap.cpu.temperature_celsius is not None:
            self.lbl_home_cpu_temp.setText(f"{snap.cpu.temperature_celsius:.0f}°C")
        if snap.gpu_nvidia.temperature_celsius is not None:
            self.lbl_home_gpu_temp.setText(f"{snap.gpu_nvidia.temperature_celsius:.0f}°C")
        used_gb = snap.memory.used_ram_mb / 1024.0
        tot_gb = snap.memory.total_ram_mb / 1024.0
        self.lbl_home_ram_stat.setText(f"{used_gb:.1f}GB / {tot_gb:.0f}GB")
