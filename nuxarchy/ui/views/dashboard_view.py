"""
NUXARCHY Dashboard View (System Vitals)
Top row: Two large RadialGauge widgets side-by-side (CPU TEMP & CLOCK, GPU TEMP & LOAD).
Middle row: Dual Fan Tachometer cards (CPU BLOWER RPM, GPU BLOWER RPM) with progress bars and PWM %.
Bottom row: VRAM USAGE, SYSTEM RAM USAGE, and BATTERY HEALTH & POWER DRAW cards.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QProgressBar,
    QGridLayout,
)
from nuxarchy.ui.widgets.radial_gauge import RadialGauge


class DashboardView(QWidget):
    """Production System Vitals dashboard."""

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(18)

        # View Header
        header = QVBoxLayout()
        header.setSpacing(4)
        title = QLabel("SYSTEM VITALS")
        title.setProperty("class", "view-title")
        subtitle = QLabel("Real-time telemetry, thermal metrics, and blower tachometers")
        subtitle.setProperty("class", "view-subtitle")
        header.addWidget(title)
        header.addWidget(subtitle)
        main_layout.addLayout(header)

        # ── Top Row: Radial Gauges (CPU & GPU) ───────────────────────────────
        gauges_card = QFrame()
        gauges_card.setProperty("class", "cyber-card")
        gauges_layout = QHBoxLayout(gauges_card)
        gauges_layout.setContentsMargins(20, 16, 20, 16)
        gauges_layout.setSpacing(30)

        self.cpu_gauge = RadialGauge(title="CPU TEMP", unit="°C", min_val=0, max_val=105)
        self.gpu_gauge = RadialGauge(title="GPU TEMP", unit="°C", min_val=0, max_val=100)

        gauges_layout.addStretch()
        gauges_layout.addWidget(self.cpu_gauge)
        gauges_layout.addSpacing(40)
        gauges_layout.addWidget(self.gpu_gauge)
        gauges_layout.addStretch()

        main_layout.addWidget(gauges_card)

        # ── Middle Row: Dual Fan Tachometer Cards ────────────────────────────
        fans_layout = QHBoxLayout()
        fans_layout.setSpacing(18)

        # CPU Fan Card
        self.cpu_fan_card = QFrame()
        self.cpu_fan_card.setProperty("class", "cyber-card")
        cf_layout = QVBoxLayout(self.cpu_fan_card)
        cf_layout.setContentsMargins(16, 14, 16, 14)
        cf_layout.setSpacing(6)

        cf_head = QHBoxLayout()
        cf_lbl = QLabel("CPU BLOWER")
        cf_lbl.setProperty("class", "card-heading")
        self.cpu_rpm_lbl = QLabel("2,100 RPM")
        self.cpu_rpm_lbl.setStyleSheet("color: #00E5FF; font-weight: 800; font-size: 13px;")
        cf_head.addWidget(cf_lbl)
        cf_head.addStretch()
        cf_head.addWidget(self.cpu_rpm_lbl)
        cf_layout.addLayout(cf_head)

        self.cpu_fan_bar = QProgressBar()
        self.cpu_fan_bar.setRange(0, 6000)
        self.cpu_fan_bar.setValue(2100)
        cf_layout.addWidget(self.cpu_fan_bar)

        self.cpu_fan_sub = QLabel("PWM Duty: 64% • Active Cooling")
        self.cpu_fan_sub.setStyleSheet("color: #8E92A4; font-size: 10px;")
        cf_layout.addWidget(self.cpu_fan_sub)

        fans_layout.addWidget(self.cpu_fan_card)

        # GPU Fan Card
        self.gpu_fan_card = QFrame()
        self.gpu_fan_card.setProperty("class", "cyber-card")
        gf_layout = QVBoxLayout(self.gpu_fan_card)
        gf_layout.setContentsMargins(16, 14, 16, 14)
        gf_layout.setSpacing(6)

        gf_head = QHBoxLayout()
        gf_lbl = QLabel("GPU BLOWER")
        gf_lbl.setProperty("class", "card-heading")
        self.gpu_rpm_lbl = QLabel("1,950 RPM")
        self.gpu_rpm_lbl.setStyleSheet("color: #00E5FF; font-weight: 800; font-size: 13px;")
        gf_head.addWidget(gf_lbl)
        gf_head.addStretch()
        gf_head.addWidget(self.gpu_rpm_lbl)
        gf_layout.addLayout(gf_head)

        self.gpu_fan_bar = QProgressBar()
        self.gpu_fan_bar.setRange(0, 6000)
        self.gpu_fan_bar.setValue(1950)
        gf_layout.addWidget(self.gpu_fan_bar)

        self.gpu_fan_sub = QLabel("PWM Duty: 64% • Direct Exhaust")
        self.gpu_fan_sub.setStyleSheet("color: #8E92A4; font-size: 10px;")
        gf_layout.addWidget(self.gpu_fan_sub)

        fans_layout.addWidget(self.gpu_fan_card)

        main_layout.addLayout(fans_layout)

        # ── Bottom Row: VRAM, RAM, Battery Meters ────────────────────────────
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(18)

        # VRAM Card
        vram_card = QFrame()
        vram_card.setProperty("class", "cyber-card")
        vr_layout = QVBoxLayout(vram_card)
        vr_layout.setContentsMargins(16, 14, 16, 14)
        vr_layout.setSpacing(6)

        vr_head = QHBoxLayout()
        vr_lbl = QLabel("VRAM USAGE")
        vr_lbl.setProperty("class", "card-heading")
        self.vram_val_lbl = QLabel("1.2 / 8.0 GB")
        self.vram_val_lbl.setStyleSheet("color: #FFFFFF; font-weight: 700; font-size: 11px;")
        vr_head.addWidget(vr_lbl)
        vr_head.addStretch()
        vr_head.addWidget(self.vram_val_lbl)
        vr_layout.addLayout(vr_head)

        self.vram_bar = QProgressBar()
        self.vram_bar.setRange(0, 100)
        self.vram_bar.setValue(15)
        vr_layout.addWidget(self.vram_bar)
        bottom_layout.addWidget(vram_card)

        # System RAM Card
        ram_card = QFrame()
        ram_card.setProperty("class", "cyber-card")
        rm_layout = QVBoxLayout(ram_card)
        rm_layout.setContentsMargins(16, 14, 16, 14)
        rm_layout.setSpacing(6)

        rm_head = QHBoxLayout()
        rm_lbl = QLabel("SYSTEM RAM")
        rm_lbl.setProperty("class", "card-heading")
        self.ram_val_lbl = QLabel("4.2 / 16.0 GB")
        self.ram_val_lbl.setStyleSheet("color: #FFFFFF; font-weight: 700; font-size: 11px;")
        rm_head.addWidget(rm_lbl)
        rm_head.addStretch()
        rm_head.addWidget(self.ram_val_lbl)
        rm_layout.addLayout(rm_head)

        self.ram_bar = QProgressBar()
        self.ram_bar.setRange(0, 100)
        self.ram_bar.setValue(26)
        rm_layout.addWidget(self.ram_bar)
        bottom_layout.addWidget(ram_card)

        # Battery Health & Power Card
        bat_card = QFrame()
        bat_card.setProperty("class", "cyber-card")
        bt_layout = QVBoxLayout(bat_card)
        bt_layout.setContentsMargins(16, 14, 16, 14)
        bt_layout.setSpacing(6)

        bt_head = QHBoxLayout()
        bt_lbl = QLabel("BATTERY HEALTH")
        bt_lbl.setProperty("class", "card-heading")
        self.bat_val_lbl = QLabel("98% • 22.5W")
        self.bat_val_lbl.setStyleSheet("color: #00E5FF; font-weight: 700; font-size: 11px;")
        bt_head.addWidget(bt_lbl)
        bt_head.addStretch()
        bt_head.addWidget(self.bat_val_lbl)
        bt_layout.addLayout(bt_head)

        self.bat_bar = QProgressBar()
        self.bat_bar.setRange(0, 100)
        self.bat_bar.setValue(98)
        bt_layout.addWidget(self.bat_bar)
        bottom_layout.addWidget(bat_card)

        main_layout.addLayout(bottom_layout)
        main_layout.addStretch()

    def update_telemetry(self, m: dict):
        """Update all telemetry visual readouts seamlessly."""
        # 1. CPU & GPU Gauges
        cpu_t = m.get("cpu_temp", 45.0)
        cpu_ghz = m.get("cpu_freq_mhz", 3200.0) / 1000.0
        cpu_usage = m.get("cpu_usage", 5.0)
        self.cpu_gauge.set_value(cpu_t, subtitle=f"{cpu_ghz:.1f} GHz • {int(cpu_usage)}%")

        gpu_t = m.get("gpu_temp", 40.0)
        gpu_usage = m.get("gpu_usage", 0.0)
        gpu_ghz = m.get("gpu_freq_mhz", 800.0) / 1000.0
        self.gpu_gauge.set_value(gpu_t, subtitle=f"{gpu_ghz:.1f} GHz • {int(gpu_usage)}%")

        # 2. Fans
        c_rpm = int(m.get("cpu_fan_rpm", 2100.0))
        g_rpm = int(m.get("gpu_fan_rpm", 1950.0))
        pwm = int(m.get("current_pwm", 64.0))
        pwm_pct = int((pwm / 255.0) * 100)

        self.cpu_rpm_lbl.setText(f"{c_rpm:,} RPM")
        self.cpu_fan_bar.setValue(c_rpm)
        self.cpu_fan_sub.setText(f"PWM: {pwm_pct}% ({pwm}/255) • Active")

        self.gpu_rpm_lbl.setText(f"{g_rpm:,} RPM")
        self.gpu_fan_bar.setValue(g_rpm)
        self.gpu_fan_sub.setText(f"PWM: {pwm_pct}% ({pwm}/255) • Active")

        # 3. VRAM
        v_used = m.get("vram_used_mb", 512.0)
        v_tot = m.get("vram_total_mb", 8192.0)
        v_pct = int((v_used / v_tot) * 100) if v_tot > 0 else 0
        self.vram_val_lbl.setText(f"{v_used / 1024:.1f} / {v_tot / 1024:.1f} GB")
        self.vram_bar.setValue(v_pct)

        # 4. RAM
        r_used = m.get("ram_used_mb", 4096.0)
        r_tot = m.get("ram_total_mb", 16384.0)
        r_pct = int((r_used / r_tot) * 100) if r_tot > 0 else 0
        self.ram_val_lbl.setText(f"{r_used / 1024:.1f} / {r_tot / 1024:.1f} GB")
        self.ram_bar.setValue(r_pct)

        # 5. Battery
        b_pct = int(m.get("battery_pct", 100.0))
        b_health = m.get("battery_health_pct", 98.0)
        p_watts = m.get("power_draw_watts", 22.0)
        self.bat_val_lbl.setText(f"Health: {b_health}% • {p_watts}W")
        self.bat_bar.setValue(b_pct)
