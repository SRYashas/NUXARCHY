"""
NUXARCHY Performance & Power View
Top section: 3 GlowCard selectors for ECO, BALANCED, and PERFORMANCE.
Middle section: Undervolting & Power Limits Panel (MSR 0x150 / RAPL TDP fallback).
Dual sliders for Core Offset (-120mV to 0mV) and Cache Offset (-120mV to 0mV), plus PL1/PL2 sliders (15W to 115W).
Bottom section: Battery Care Optimizer (80% / 100% toggle).
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QSlider,
    QPushButton,
    QCheckBox,
    QMessageBox,
)
from nuxarchy.ui.widgets.glow_card import GlowCard
from nuxarchy.services.daemon_client import DaemonClient


class PerformanceView(QWidget):
    """Performance profiling, CPU undervolt/RAPL tuning, and battery care."""

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.client = DaemonClient.instance()
        self._setup_ui()
        self.refresh_state()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(18)

        # Header
        header = QVBoxLayout()
        header.setSpacing(4)
        title = QLabel("PERFORMANCE & POWER")
        title.setProperty("class", "view-title")
        subtitle = QLabel("ACPI platform thermal envelopes, CPU voltage tuning, and Battery Care")
        subtitle.setProperty("class", "view-subtitle")
        header.addWidget(title)
        header.addWidget(subtitle)
        main_layout.addLayout(header)

        # ── Top Section: 3 GlowCard Selectors ────────────────────────────────
        profiles_layout = QHBoxLayout()
        profiles_layout.setSpacing(14)

        self.card_eco = GlowCard(
            title="ECO / QUIET",
            subtitle="Low acoustics & low TDP for maximum battery efficiency",
            icon_text="🌱",
            badge_text="POWERSAVE",
            accent_color="#00E5FF",
        )
        self.card_eco.clicked.connect(lambda: self._select_profile("eco"))
        profiles_layout.addWidget(self.card_eco)

        self.card_balanced = GlowCard(
            title="BALANCED",
            subtitle="Default OEM acoustic and dynamic thermal envelope",
            icon_text="⚖️",
            badge_text="OEM DEFAULT",
            accent_color="#00E5FF",
        )
        self.card_balanced.clicked.connect(lambda: self._select_profile("balanced"))
        profiles_layout.addWidget(self.card_balanced)

        self.card_perf = GlowCard(
            title="PERFORMANCE",
            subtitle="Max TDP envelope, aggressive fan curve, dynamic boost",
            icon_text="🚀",
            badge_text="MAX CLOCKS",
            accent_color="#FF0552",
        )
        self.card_perf.clicked.connect(lambda: self._select_profile("performance"))
        profiles_layout.addWidget(self.card_perf)

        main_layout.addLayout(profiles_layout)

        # ── Middle Section: Undervolting & Power Limits Panel ────────────────
        tuning_card = QFrame()
        tuning_card.setProperty("class", "cyber-card")
        tune_layout = QVBoxLayout(tuning_card)
        tune_layout.setContentsMargins(20, 18, 20, 18)
        tune_layout.setSpacing(14)

        # Panel Header with Capability Badge
        tune_header = QHBoxLayout()
        t_title = QLabel("HARDWARE VOLTAGE & TDP CLAMPING")
        t_title.setProperty("class", "card-heading")
        tune_header.addWidget(t_title)
        tune_header.addStretch()

        self.cap_badge = QLabel("DETECTING CAPABILITIES...")
        self.cap_badge.setStyleSheet(
            "background-color: #1C1F2E; color: #00E5FF; padding: 4px 10px; "
            "border-radius: 4px; font-weight: 700; font-size: 10px; border: 1px solid #2B3045;"
        )
        tune_header.addWidget(self.cap_badge)
        tune_layout.addLayout(tune_header)

        # Sliders Grid
        # Core Slider (-120mV to 0mV)
        core_box = QHBoxLayout()
        core_lbl = QLabel("CPU CORE OFFSET:")
        core_lbl.setFixedWidth(150)
        core_lbl.setStyleSheet("color: #FFFFFF; font-weight: 600;")
        self.core_slider = QSlider(Qt.Orientation.Horizontal)
        self.core_slider.setRange(-120, 0)
        self.core_slider.setValue(0)
        self.core_val_lbl = QLabel("0 mV")
        self.core_val_lbl.setFixedWidth(65)
        self.core_val_lbl.setStyleSheet("color: #00E5FF; font-weight: 700;")
        self.core_slider.valueChanged.connect(lambda v: self.core_val_lbl.setText(f"{v} mV"))

        core_box.addWidget(core_lbl)
        core_box.addWidget(self.core_slider)
        core_box.addWidget(self.core_val_lbl)
        tune_layout.addLayout(core_box)

        # Cache Slider (-120mV to 0mV)
        cache_box = QHBoxLayout()
        cache_lbl = QLabel("CPU CACHE OFFSET:")
        cache_lbl.setFixedWidth(150)
        cache_lbl.setStyleSheet("color: #FFFFFF; font-weight: 600;")
        self.cache_slider = QSlider(Qt.Orientation.Horizontal)
        self.cache_slider.setRange(-120, 0)
        self.cache_slider.setValue(0)
        self.cache_val_lbl = QLabel("0 mV")
        self.cache_val_lbl.setFixedWidth(65)
        self.cache_val_lbl.setStyleSheet("color: #00E5FF; font-weight: 700;")
        self.cache_slider.valueChanged.connect(lambda v: self.cache_val_lbl.setText(f"{v} mV"))

        cache_box.addWidget(cache_lbl)
        cache_box.addWidget(self.cache_slider)
        cache_box.addWidget(self.cache_val_lbl)
        tune_layout.addLayout(cache_box)

        # PL1 Wattage Slider (15W to 115W)
        pl1_box = QHBoxLayout()
        pl1_lbl = QLabel("PL1 SUSTAINED TDP:")
        pl1_lbl.setFixedWidth(150)
        pl1_lbl.setStyleSheet("color: #FFFFFF; font-weight: 600;")
        self.pl1_slider = QSlider(Qt.Orientation.Horizontal)
        self.pl1_slider.setRange(15, 115)
        self.pl1_slider.setValue(45)
        self.pl1_val_lbl = QLabel("45 W")
        self.pl1_val_lbl.setFixedWidth(65)
        self.pl1_val_lbl.setStyleSheet("color: #00E5FF; font-weight: 700;")
        self.pl1_slider.valueChanged.connect(lambda v: self.pl1_val_lbl.setText(f"{v} W"))

        pl1_box.addWidget(pl1_lbl)
        pl1_box.addWidget(self.pl1_slider)
        pl1_box.addWidget(self.pl1_val_lbl)
        tune_layout.addLayout(pl1_box)

        # PL2 Wattage Slider (15W to 115W)
        pl2_box = QHBoxLayout()
        pl2_lbl = QLabel("PL2 PEAK BOOST TDP:")
        pl2_lbl.setFixedWidth(150)
        pl2_lbl.setStyleSheet("color: #FFFFFF; font-weight: 600;")
        self.pl2_slider = QSlider(Qt.Orientation.Horizontal)
        self.pl2_slider.setRange(15, 115)
        self.pl2_slider.setValue(65)
        self.pl2_val_lbl = QLabel("65 W")
        self.pl2_val_lbl.setFixedWidth(65)
        self.pl2_val_lbl.setStyleSheet("color: #00E5FF; font-weight: 700;")
        self.pl2_slider.valueChanged.connect(lambda v: self.pl2_val_lbl.setText(f"{v} W"))

        pl2_box.addWidget(pl2_lbl)
        pl2_box.addWidget(self.pl2_slider)
        pl2_box.addWidget(self.pl2_val_lbl)
        tune_layout.addLayout(pl2_box)

        # Action Button
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        self.apply_tuning_btn = QPushButton("APPLY TUNING")
        self.apply_tuning_btn.setProperty("class", "cyber-btn-primary")
        self.apply_tuning_btn.clicked.connect(self._apply_tuning)
        btn_box.addWidget(self.apply_tuning_btn)
        tune_layout.addLayout(btn_box)

        main_layout.addWidget(tuning_card)

        # ── Bottom Section: Battery Care Optimizer ───────────────────────────
        battery_card = QFrame()
        battery_card.setProperty("class", "cyber-card")
        bat_layout = QHBoxLayout(battery_card)
        bat_layout.setContentsMargins(20, 16, 20, 16)

        bat_info = QVBoxLayout()
        bat_title = QLabel("BATTERY CARE OPTIMIZER")
        bat_title.setProperty("class", "card-heading")
        bat_desc = QLabel("Cap maximum charge at 80% to prolong battery lifespan and reduce chemical wear")
        bat_desc.setStyleSheet("color: #8E92A4; font-size: 11px;")
        bat_info.addWidget(bat_title)
        bat_info.addWidget(bat_desc)
        bat_layout.addLayout(bat_info)

        bat_layout.addStretch()

        self.battery_toggle = QCheckBox("LIMIT CHARGE TO 80%")
        self.battery_toggle.setStyleSheet("color: #00E5FF; font-weight: 700; font-size: 11px;")
        self.battery_toggle.toggled.connect(self._on_battery_toggle)
        bat_layout.addWidget(self.battery_toggle)

        main_layout.addWidget(battery_card)
        main_layout.addStretch()

    def refresh_state(self):
        # 1. Platform Profile
        cur_prof = self.client.get_platform_profile().lower()
        self.card_eco.set_active("low" in cur_prof or "quiet" in cur_prof or "eco" in cur_prof)
        self.card_balanced.set_active("balanced" in cur_prof or "default" in cur_prof)
        self.card_perf.set_active("perf" in cur_prof or "extreme" in cur_prof)

        # 2. Undervolt Status
        st = self.client.get_undervolt_status()
        is_supported = st.get("supported") == "true"
        reason = st.get("reason", "")

        if is_supported:
            self.cap_badge.setText("MSR 0x150 UNLOCKED")
            self.cap_badge.setStyleSheet(
                "background-color: rgba(0, 229, 255, 0.15); color: #00E5FF; "
                "padding: 4px 10px; border-radius: 4px; font-weight: 700; border: 1px solid #00E5FF;"
            )
        else:
            self.cap_badge.setText("LOCKED BY PLUNDERVOLT • USING RAPL FALLBACK")
            self.cap_badge.setStyleSheet(
                "background-color: rgba(255, 179, 0, 0.15); color: #FFB300; "
                "padding: 4px 10px; border-radius: 4px; font-weight: 700; border: 1px solid #FFB300;"
            )

        core_mv = int(st.get("core_offset_mv", 0))
        cache_mv = int(st.get("cache_offset_mv", 0))
        pl1 = int(st.get("pl1_watts", 45))
        pl2 = int(st.get("pl2_watts", 65))

        self.core_slider.setValue(core_mv)
        self.cache_slider.setValue(cache_mv)
        self.pl1_slider.setValue(pl1)
        self.pl2_slider.setValue(pl2)

        # 3. Battery
        bat_lim = self.client.get_battery_limit()
        self.battery_toggle.blockSignals(True)
        self.battery_toggle.setChecked(bat_lim <= 85)
        self.battery_toggle.blockSignals(False)

    def _select_profile(self, profile: str):
        self.client.set_platform_profile(profile)
        self.card_eco.set_active(profile == "eco")
        self.card_balanced.set_active(profile == "balanced")
        self.card_perf.set_active(profile == "performance")

    def _apply_tuning(self):
        core = self.core_slider.value()
        cache = self.cache_slider.value()
        pl1 = self.pl1_slider.value()
        pl2 = self.pl2_slider.value()

        ok_uv = self.client.set_undervolt_offset(core, cache)
        ok_rapl = self.client.set_power_limits(pl1, pl2)

        msg = f"Tuning Applied:\n• Core Offset: {core} mV\n• Cache Offset: {cache} mV\n• PL1 / PL2: {pl1}W / {pl2}W"
        QMessageBox.information(self, "Tuning Applied", msg)

    def _on_battery_toggle(self, checked: bool):
        limit = 80 if checked else 100
        self.client.set_battery_limit(limit)
