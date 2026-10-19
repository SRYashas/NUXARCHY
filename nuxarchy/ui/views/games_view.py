"""
NUXARCHY: Game Management & Booster View
Discovers installed Steam and native games, manages per-game performance profiles,
and provides one-click launching with automatic discrete GPU offloading.
"""

import subprocess
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QScrollArea, QGridLayout, QCheckBox, QComboBox, QMessageBox
)
from PySide6.QtCore import Qt

from nuxarchy.backend.capability import HardwareCapabilities
from nuxarchy.backend.games.library_scanner import GameLibraryScanner, GameEntry


class GamesView(QWidget):
    def __init__(self, caps: HardwareCapabilities, parent=None):
        super().__init__(parent)
        self.caps = caps
        self.scanner = GameLibraryScanner()
        self.games = self.scanner.scan_all()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        # Header
        header = QHBoxLayout()
        header_text = QVBoxLayout()
        title = QLabel("MY GAMES & APPLICATION BOOSTER")
        title.setStyleSheet("color: #FFFFFF; font-size: 20px; font-weight: 800; letter-spacing: 1px;")
        header_text.addWidget(title)

        sub = QLabel(f"Indexed {len(self.games)} installed games. Configure per-game GPU routing and performance triggers.")
        sub.setStyleSheet("color: #9CA3AF; font-size: 13px;")
        header_text.addWidget(sub)
        header.addLayout(header_text)

        header.addStretch()

        btn_rescan = QPushButton("RE-SCAN GAMES")
        btn_rescan.setProperty("class", "secondaryButton")
        btn_rescan.clicked.connect(self._rescan_games)
        header.addWidget(btn_rescan)

        layout.addLayout(header)

        # Scrollable Game Cards Grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        self.grid_layout = QVBoxLayout(container)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(12)

        self._populate_game_cards()

        scroll.setWidget(container)
        layout.addWidget(scroll)

    def _populate_game_cards(self):
        # Clear existing
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for game in self.games:
            card = QFrame()
            card.setProperty("class", "cardFrame")
            c_layout = QHBoxLayout(card)
            c_layout.setContentsMargins(16, 14, 16, 14)
            c_layout.setSpacing(16)

            # Left: Game Icon / Platform Pill
            pill = QLabel(game.source.upper())
            pill.setStyleSheet("""
                background-color: rgba(157, 78, 221, 0.15);
                color: #9D4EDD;
                font-size: 10px;
                font-weight: 800;
                padding: 6px 10px;
                border-radius: 6px;
                border: 1px solid rgba(157, 78, 221, 0.3);
            """)
            c_layout.addWidget(pill)

            # Center: Title & Size
            info_layout = QVBoxLayout()
            lbl_name = QLabel(game.name)
            lbl_name.setStyleSheet("color: #FFFFFF; font-size: 15px; font-weight: 700;")
            info_layout.addWidget(lbl_name)

            lbl_sub = QLabel(f"Storage: {game.installed_size_mb:,.0f} MB • Launch ID: {game.id}")
            lbl_sub.setStyleSheet("color: #6B7280; font-size: 11px;")
            info_layout.addWidget(lbl_sub)
            c_layout.addLayout(info_layout)

            c_layout.addStretch()

            # GPU Checkbox
            chk_gpu = QCheckBox("NVIDIA dGPU Boost")
            chk_gpu.setChecked(game.use_dedicated_gpu)
            chk_gpu.stateChanged.connect(lambda state, g=game: setattr(g, "use_dedicated_gpu", state == Qt.Checked))
            c_layout.addWidget(chk_gpu)

            # Profile Selector
            combo_prof = QComboBox()
            combo_prof.addItems(["Performance", "Balanced", "Quiet"])
            combo_prof.setCurrentText(game.performance_profile.capitalize())
            combo_prof.currentTextChanged.connect(lambda text, g=game: setattr(g, "performance_profile", text.lower()))
            c_layout.addWidget(combo_prof)

            # Launch Button
            btn_play = QPushButton("PLAY")
            btn_play.setProperty("class", "primaryButton")
            btn_play.clicked.connect(lambda checked, g=game: self._launch_game(g))
            c_layout.addWidget(btn_play)

            self.grid_layout.addWidget(card)

        self.grid_layout.addStretch()

    def _rescan_games(self):
        self.games = self.scanner.scan_all()
        self._populate_game_cards()
        QMessageBox.information(self, "Game Scanner", f"Scan complete. Indexed {len(self.games)} titles.")

    def _launch_game(self, game: GameEntry):
        cmd = self.scanner.build_launch_command(game)
        try:
            # Launch detached process
            subprocess.Popen(cmd, shell=True)
            QMessageBox.information(self, "Launching Game", f"Launching '{game.name}' with:\n{cmd}")
        except Exception as e:
            QMessageBox.warning(self, "Launch Error", f"Failed to launch '{game.name}': {str(e)}")
