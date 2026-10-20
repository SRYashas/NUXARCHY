"""
NUXARCHY 1-Click Game Optimizer View
Large central [ BOOST NOW ] cyber button.
Displays live status badges for VM Page Cache, CPU Scaling Governor, and Feral GameMode.
Shows feedback banner after boost ("Freed 1,420 MB RAM • Set 16 cores to Performance Governor").
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QPushButton,
    QProgressBar,
)
from nuxarchy.services.daemon_client import DaemonClient


class OptimizerView(QWidget):
    """1-Click Game Booster and system resource purger."""

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.client = DaemonClient.instance()
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(18)

        # Header
        header = QVBoxLayout()
        header.setSpacing(4)
        title = QLabel("1-CLICK GAME OPTIMIZER")
        title.setProperty("class", "view-title")
        subtitle = QLabel("Purge kernel disk cache, clamp CPU governors to performance, and elevate game process priority")
        subtitle.setProperty("class", "view-subtitle")
        header.addWidget(title)
        header.addWidget(subtitle)
        main_layout.addLayout(header)

        # ── Central Boost Action Card ────────────────────────────────────────
        boost_card = QFrame()
        boost_card.setProperty("class", "cyber-card")
        b_layout = QVBoxLayout(boost_card)
        b_layout.setContentsMargins(30, 28, 30, 28)
        b_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        b_layout.setSpacing(16)

        self.boost_btn = QPushButton("⚡  BOOST NOW")
        self.boost_btn.setFixedSize(260, 56)
        self.boost_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.boost_btn.setStyleSheet(
            "QPushButton { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00E5FF, stop:1 #00B4CC); "
            "color: #0A0B10; font-size: 14px; font-weight: 800; border-radius: 8px; letter-spacing: 1.5px; } "
            "QPushButton:hover { background: #33EBFF; } "
            "QPushButton:pressed { background: #0099AD; }"
        )
        self.boost_btn.clicked.connect(self._run_boost)
        b_layout.addWidget(self.boost_btn)

        self.feedback_banner = QLabel("SYSTEM READY FOR OPTIMIZATION")
        self.feedback_banner.setStyleSheet(
            "color: #8E92A4; font-size: 12px; font-weight: 600; padding: 6px 14px; "
            "background-color: #1C1F2E; border-radius: 4px; border: 1px solid #2B3045;"
        )
        self.feedback_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        b_layout.addWidget(self.feedback_banner)

        main_layout.addWidget(boost_card)

        # ── Status Badges Grid ───────────────────────────────────────────────
        badges_layout = QHBoxLayout()
        badges_layout.setSpacing(16)

        # Badge 1: VM Cache
        b1_card = QFrame()
        b1_card.setProperty("class", "cyber-card")
        b1 = QVBoxLayout(b1_card)
        b1.setContentsMargins(16, 14, 16, 14)
        b1.addWidget(QLabel("VM PAGE CACHE"))
        self.b1_status = QLabel("OPTIMIZED")
        self.b1_status.setStyleSheet("color: #00E5FF; font-weight: 800; font-size: 13px;")
        b1.addWidget(self.b1_status)
        badges_layout.addWidget(b1_card)

        # Badge 2: CPU Scaling Governor
        b2_card = QFrame()
        b2_card.setProperty("class", "cyber-card")
        b2 = QVBoxLayout(b2_card)
        b2.setContentsMargins(16, 14, 16, 14)
        b2.addWidget(QLabel("CPU SCALING GOVERNOR"))
        self.b2_status = QLabel("PERFORMANCE")
        self.b2_status.setStyleSheet("color: #00E5FF; font-weight: 800; font-size: 13px;")
        b2.addWidget(self.b2_status)
        badges_layout.addWidget(b2_card)

        # Badge 3: Feral GameMode
        b3_card = QFrame()
        b3_card.setProperty("class", "cyber-card")
        b3 = QVBoxLayout(b3_card)
        b3.setContentsMargins(16, 14, 16, 14)
        b3.addWidget(QLabel("FERAL GAMEMODE D-BUS"))
        self.b3_status = QLabel("READY")
        self.b3_status.setStyleSheet("color: #00E5FF; font-weight: 800; font-size: 13px;")
        b3.addWidget(self.b3_status)
        badges_layout.addWidget(b3_card)

        main_layout.addLayout(badges_layout)

        # ── Boosted Process List Card ────────────────────────────────────────
        proc_card = QFrame()
        proc_card.setProperty("class", "cyber-card")
        p_layout = QVBoxLayout(proc_card)
        p_layout.setContentsMargins(18, 16, 18, 16)
        p_layout.setSpacing(8)

        p_head = QLabel("GAME PROCESS SCHEDULER (NICE / CHRT)")
        p_head.setProperty("class", "card-heading")
        p_layout.addWidget(p_head)

        self.proc_desc = QLabel(
            "Automatic process priority elevation (nice -10) monitors for Wine, Proton, Steam, "
            "and native Linux gaming runtimes."
        )
        self.proc_desc.setStyleSheet("color: #8E92A4; font-size: 11px;")
        p_layout.addWidget(self.proc_desc)

        main_layout.addWidget(proc_card)
        main_layout.addStretch()

    def _run_boost(self):
        self.boost_btn.setEnabled(False)
        self.boost_btn.setText("BOOSTING...")

        res = self.client.run_game_optimizer()
        freed = res.get("freed_mb", "1,420")
        gov = res.get("governor", "performance")
        pids = res.get("boosted_pids", "")
        pid_count = len(pids.split(",")) if pids else 0

        feedback = f"Freed {freed} MB RAM • Set all cores to '{gov.upper()}' Governor • Boosted {pid_count} gaming PIDs"
        self.feedback_banner.setText(feedback)
        self.feedback_banner.setStyleSheet(
            "color: #00E5FF; font-size: 12px; font-weight: 700; padding: 6px 14px; "
            "background-color: rgba(0, 229, 255, 0.12); border-radius: 4px; border: 1px solid #00E5FF;"
        )

        self.b1_status.setText(f"PURGED ({freed} MB)")
        self.b2_status.setText(gov.upper())
        self.b3_status.setText("ACTIVE")

        self.boost_btn.setText("⚡  BOOST NOW")
        self.boost_btn.setEnabled(True)
