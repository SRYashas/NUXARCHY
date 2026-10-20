"""
NUXARCHY Graphics / MUX Switcher View
Three GlowCard selectors: HYBRID, DISCRETE, INTEGRATED.
Shows active backend (supergfxctl or envycontrol) and confirmation dialog with reboot guardrails.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QMessageBox,
)
from nuxarchy.ui.widgets.glow_card import GlowCard
from nuxarchy.services.daemon_client import DaemonClient


class GpuView(QWidget):
    """Graphics multiplexer and hybrid Optimus display switcher."""

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.client = DaemonClient.instance()
        self._current_mode = "hybrid"
        self._setup_ui()
        self.refresh_state()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(18)

        # Header
        header = QVBoxLayout()
        header.setSpacing(4)
        title = QLabel("GRAPHICS & MUX SWITCHER")
        title.setProperty("class", "view-title")
        subtitle = QLabel("Hardware display multiplexer and dynamic GPU routing")
        subtitle.setProperty("class", "view-subtitle")
        header.addWidget(title)
        header.addWidget(subtitle)
        main_layout.addLayout(header)

        # Backend Status Banner
        self.status_banner = QFrame()
        self.status_banner.setProperty("class", "cyber-card")
        sb_layout = QHBoxLayout(self.status_banner)
        sb_layout.setContentsMargins(16, 12, 16, 12)

        sb_lbl = QLabel("ACTIVE BACKEND:")
        sb_lbl.setProperty("class", "card-heading")
        sb_layout.addWidget(sb_lbl)

        self.backend_val_lbl = QLabel("supergfxctl (D-Bus)")
        self.backend_val_lbl.setStyleSheet("color: #00E5FF; font-weight: 700;")
        sb_layout.addWidget(self.backend_val_lbl)

        sb_layout.addStretch()

        self.reboot_badge = QLabel("ACTIVE")
        self.reboot_badge.setStyleSheet(
            "background-color: #1C1F2E; color: #00E5FF; padding: 3px 8px; "
            "border-radius: 4px; font-weight: 700; font-size: 10px;"
        )
        sb_layout.addWidget(self.reboot_badge)
        main_layout.addWidget(self.status_banner)

        # ── Three GlowCard Selectors ─────────────────────────────────────────
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)

        self.card_hybrid = GlowCard(
            title="HYBRID (OPTIMUS)",
            subtitle="Display driven by iGPU, dGPU activates dynamically for games/3D workloads",
            icon_text="🔄",
            badge_text="DYNAMIC DUAL",
            accent_color="#00E5FF",
        )
        self.card_hybrid.clicked.connect(lambda: self._request_mode("hybrid"))
        cards_layout.addWidget(self.card_hybrid)

        self.card_discrete = GlowCard(
            title="DISCRETE (DEDICATED)",
            subtitle="Internal panel wired directly to dGPU. Maximum FPS, zero Optimus latency",
            icon_text="🎮",
            badge_text="DIRECT MUX",
            accent_color="#FF0552",
        )
        self.card_discrete.clicked.connect(lambda: self._request_mode("dedicated"))
        cards_layout.addWidget(self.card_discrete)

        self.card_integrated = GlowCard(
            title="INTEGRATED (IGPU ONLY)",
            subtitle="Completely powers down dGPU for whisper-quiet travel & maximum battery life",
            icon_text="🔋",
            badge_text="BATTERY SAVER",
            accent_color="#00E5FF",
        )
        self.card_integrated.clicked.connect(lambda: self._request_mode("integrated"))
        cards_layout.addWidget(self.card_integrated)

        main_layout.addLayout(cards_layout)

        # Info Note
        note_card = QFrame()
        note_card.setProperty("class", "cyber-card")
        nc_layout = QVBoxLayout(note_card)
        nc_layout.setContentsMargins(18, 14, 18, 14)
        nc_title = QLabel("DISPLAY SESSION GUARDRAILS")
        nc_title.setProperty("class", "card-heading")
        nc_desc = QLabel(
            "Hardware display multiplexer switching requires unbinding kernel GPU drivers. "
            "A system reboot or display manager restart (GDM/SDDM) is mandatory to apply the hardware bus transition."
        )
        nc_desc.setStyleSheet("color: #8E92A4; font-size: 11px;")
        nc_desc.setWordWrap(True)
        nc_layout.addWidget(nc_title)
        nc_layout.addWidget(nc_desc)
        main_layout.addWidget(note_card)

        main_layout.addStretch()

    def refresh_state(self):
        st = self.client.get_gpu_status()
        self._current_mode = st.get("current_mode", "hybrid").lower()
        backend = st.get("backend", "simulated")
        reboot_req = st.get("requires_reboot", "false") == "true"

        self.backend_val_lbl.setText(f"{backend.upper()}")
        if reboot_req:
            self.reboot_badge.setText("REBOOT REQUIRED")
            self.reboot_badge.setStyleSheet(
                "background-color: rgba(255, 5, 82, 0.2); color: #FF0552; "
                "padding: 3px 8px; border-radius: 4px; font-weight: 700; border: 1px solid #FF0552;"
            )
        else:
            self.reboot_badge.setText("APPLIED")
            self.reboot_badge.setStyleSheet(
                "background-color: rgba(0, 229, 255, 0.15); color: #00E5FF; "
                "padding: 3px 8px; border-radius: 4px; font-weight: 700; border: 1px solid #00E5FF;"
            )

        self.card_hybrid.set_active("hybrid" in self._current_mode)
        self.card_discrete.set_active("discrete" in self._current_mode or "dedicated" in self._current_mode or "nvidia" in self._current_mode)
        self.card_integrated.set_active("integrated" in self._current_mode)

    def _request_mode(self, mode: str):
        if mode == self._current_mode:
            return

        confirm = QMessageBox.question(
            self,
            "Confirm GPU Mode Switch",
            f"Switching GPU architecture to '{mode.upper()}' requires a display session restart or system reboot.\n\n"
            "Would you like to apply this hardware switch now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirm == QMessageBox.StandardButton.Yes:
            ok = self.client.set_gpu_mode(mode)
            if ok:
                self.refresh_state()
                QMessageBox.information(
                    self,
                    "GPU Mode Scheduled",
                    f"GPU mode has been set to '{mode.upper()}'. Please reboot your laptop or restart your display manager to complete the hardware switch.",
                )
            else:
                QMessageBox.warning(self, "GPU Switch Failed", "Failed to switch GPU mode via root daemon.")
