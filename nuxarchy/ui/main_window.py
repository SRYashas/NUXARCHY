"""
NUXARCHY Master Window
Frameless/dark cyber-styled main window with 220px left navigation rail,
OMEN diamond logo header, live DAEMON ONLINE / OFFLINE pill badge,
navigation items for all 7 views, 1500ms QTimer telemetry loop,
and D-Bus omen_hotkey_pressed visibility toggle.
"""

import os
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QIcon, QFont, QColor
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QStackedWidget,
    QPushButton,
    QLabel,
    QFrame,
    QButtonGroup,
    QScrollArea,
)

from nuxarchy.services.daemon_client import DaemonClient
from nuxarchy.ui.views.dashboard_view import DashboardView
from nuxarchy.ui.views.performance_view import PerformanceView
from nuxarchy.ui.views.thermal_view import ThermalView
from nuxarchy.ui.views.gpu_view import GpuView
from nuxarchy.ui.views.lighting_view import LightingView
from nuxarchy.ui.views.network_booster_view import NetworkBoosterView
from nuxarchy.ui.views.optimizer_view import OptimizerView


class MainWindow(QMainWindow):
    """Production Master Window for NUXARCHY."""

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.client = DaemonClient.instance()

        self.setWindowTitle("NUXARCHY // Linux Gaming Hub")
        self.resize(1200, 780)
        self.setMinimumSize(1080, 700)

        self._setup_ui()
        self._setup_hotkey()
        self._setup_telemetry_timer()

    def _setup_ui(self):
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Left Navigation Rail (width: 220px, bg #0E1017) ───────────────────
        nav_rail = QFrame()
        nav_rail.setObjectName("navSidebar")
        nav_rail.setFixedWidth(220)
        nav_layout = QVBoxLayout(nav_rail)
        nav_layout.setContentsMargins(0, 0, 0, 16)
        nav_layout.setSpacing(4)

        # Header: OMEN Diamond Logo + Title + Status Pill
        logo_container = QWidget()
        logo_container.setObjectName("navLogoContainer")
        lc_layout = QVBoxLayout(logo_container)
        lc_layout.setContentsMargins(18, 20, 18, 16)
        lc_layout.setSpacing(8)

        brand_row = QHBoxLayout()
        diamond_lbl = QLabel("◆")
        diamond_lbl.setStyleSheet("color: #FF0552; font-size: 20px; font-weight: 900;")
        brand_row.addWidget(diamond_lbl)

        title_lbl = QLabel("NUXARCHY")
        title_lbl.setObjectName("navLogoTitle")
        brand_row.addWidget(title_lbl)
        brand_row.addStretch()
        lc_layout.addLayout(brand_row)

        # Status Pill (DAEMON ONLINE in green/cyan, OFFLINE in red)
        self.status_pill = QLabel("DAEMON ONLINE" if self.client.is_connected() else "DAEMON OFFLINE")
        self.status_pill.setObjectName("navDaemonBadge")
        self.status_pill.setProperty("online", "true" if self.client.is_connected() else "false")
        self.status_pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lc_layout.addWidget(self.status_pill)

        nav_layout.addWidget(logo_container)
        nav_layout.addSpacing(8)

        # Navigation Buttons Group
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        nav_items = [
            ("SYSTEM VITALS", "📊"),
            ("PERFORMANCE", "⚡"),
            ("THERMAL & FANS", "❄️"),
            ("GRAPHICS SWITCHER", "🎮"),
            ("LIGHT STUDIO", "🌈"),
            ("NETWORK BOOSTER", "🌐"),
            ("GAME OPTIMIZER", "🚀"),
        ]

        self.nav_buttons = []
        for idx, (label, icon) in enumerate(nav_items):
            btn = QPushButton(f"  {icon}  {label}")
            btn.setProperty("class", "nav-btn")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.nav_group.addButton(btn, idx)
            btn.clicked.connect(lambda checked, i=idx: self._on_nav_clicked(i))
            nav_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        nav_layout.addStretch()

        # Footer info
        ver_lbl = QLabel("v2.0.0 • Linux Native")
        ver_lbl.setStyleSheet("color: #4A5068; font-size: 10px; padding-left: 20px;")
        nav_layout.addWidget(ver_lbl)

        main_layout.addWidget(nav_rail)

        # ── Right Stacked View Area ──────────────────────────────────────────
        content_area = QWidget()
        ca_layout = QVBoxLayout(content_area)
        ca_layout.setContentsMargins(0, 0, 0, 0)
        ca_layout.setSpacing(0)

        self.stack = QStackedWidget()

        # Instantiate 7 Views
        self.dashboard_view = DashboardView()
        self.performance_view = PerformanceView()
        self.thermal_view = ThermalView()
        self.gpu_view = GpuView()
        self.lighting_view = LightingView()
        self.network_booster_view = NetworkBoosterView()
        self.optimizer_view = OptimizerView()

        self.stack.addWidget(self.dashboard_view)          # 0: SYSTEM VITALS
        self.stack.addWidget(self.performance_view)        # 1: PERFORMANCE
        self.stack.addWidget(self.thermal_view)            # 2: THERMAL & FANS
        self.stack.addWidget(self.gpu_view)                # 3: GRAPHICS SWITCHER
        self.stack.addWidget(self.lighting_view)           # 4: LIGHT STUDIO
        self.stack.addWidget(self.network_booster_view)    # 5: NETWORK BOOSTER
        self.stack.addWidget(self.optimizer_view)          # 6: GAME OPTIMIZER

        ca_layout.addWidget(self.stack)
        main_layout.addWidget(content_area)

        # Default selection: Dashboard
        self.nav_buttons[0].setChecked(True)
        self.stack.setCurrentIndex(0)

    def _on_nav_clicked(self, idx: int):
        self.stack.setCurrentIndex(idx)
        # Refresh current view
        widget = self.stack.currentWidget()
        if hasattr(widget, "refresh_state"):
            widget.refresh_state()

    def _setup_hotkey(self):
        """Connect to D-Bus signal omen_hotkey_pressed to toggle window visibility."""
        def on_hotkey_signal():
            self._toggle_visibility()

        self.client.register_hotkey_callback(on_hotkey_signal)

    @pyqtSlot()
    def _toggle_visibility(self):
        if self.isVisible() and not self.isMinimized():
            self.hide()
        else:
            self.showNormal()
            self.raise_()
            self.activateWindow()

    def _setup_telemetry_timer(self):
        """Run a QTimer every 1500ms querying daemon_client.get_telemetry_metrics()."""
        self.timer = QTimer(self)
        self.timer.setInterval(1500)
        self.timer.timeout.connect(self._poll_telemetry)
        self.timer.start()
        # Immediate first tick
        self._poll_telemetry()

    def _poll_telemetry(self):
        metrics = self.client.get_telemetry_metrics()

        # Update daemon status pill
        is_conn = self.client.is_connected()
        self.status_pill.setText("DAEMON ONLINE" if is_conn else "DAEMON OFFLINE")
        self.status_pill.setProperty("online", "true" if is_conn else "false")
        self.status_pill.setStyle(self.status_pill.style())

        # Broadcast to active views
        self.dashboard_view.update_telemetry(metrics)
        self.thermal_view.update_telemetry(metrics)
