"""
OMEN Gaming Hub: Master Window & Layout Architecture (Pixel-Perfect Recreation)
Matches the exact sidebar items, badges, OMEN 16 device tree, Optimizer
expandable sub-items, and top tab bar from the reference screenshots.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel,
    QPushButton, QStackedWidget, QButtonGroup, QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from nuxarchy.backend.capability import HardwareCapabilities
from nuxarchy.backend.telemetry.system_monitor import SystemMonitorThread, SystemSnapshot
from nuxarchy.services.profile_manager import ProfileManager

from nuxarchy.ui.views.home_view import HomeView
from nuxarchy.ui.views.dashboard_view import DashboardView
from nuxarchy.ui.views.performance_view import PerformanceView
from nuxarchy.ui.views.thermal_view import ThermalView
from nuxarchy.ui.views.gpu_view import GpuView
from nuxarchy.ui.views.lighting_view import LightingView
from nuxarchy.ui.views.games_view import GamesView
from nuxarchy.ui.views.network_booster_view import NetworkBoosterView
from nuxarchy.ui.views.diagnostics_view import DiagnosticsView
from nuxarchy.ui.views.settings_view import SettingsView
from nuxarchy.ui.views.optimizer_view import OptimizerView


# Stack index constants for clarity
_HOME = 0
_VITALS = 1
_PERF = 2
_LIGHTING = 3
_GPU = 4
_NET_BOOSTER = 5
_GAMES = 6
_DIAG = 7
_SETTINGS = 8
_OPTIMIZER = 9


class MainWindow(QMainWindow):
    def __init__(self, caps: HardwareCapabilities, profile_mgr: ProfileManager, parent=None):
        super().__init__(parent)
        self.caps = caps
        self.profile_mgr = profile_mgr

        self.setWindowTitle("NUXARCHY")
        self.resize(1280, 800)
        self.setMinimumSize(1120, 720)

        import os
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "nuxarchy_logo.png")
        if os.path.exists(logo_path):
            self.setWindowIcon(QIcon(logo_path))

        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Exact Left Sidebar
        sidebar = self._build_sidebar()
        main_layout.addWidget(sidebar)

        # 2. Right Content Pane
        content_pane = QWidget()
        self.content_layout = QVBoxLayout(content_pane)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        # Top Horizontal Sub-Nav Tabs
        self.top_tabs = self._build_top_tab_bar()
        self.content_layout.addWidget(self.top_tabs)

        # Views Stack
        self.stack = QStackedWidget()
        self.home_view = HomeView(caps, on_device_click=lambda: self._select_device_tab(0))
        self.vitals_view = DashboardView(caps)
        self.perf_view = PerformanceView(caps)
        self.lighting_view = LightingView(caps)
        self.gpu_view = GpuView(caps)
        self.net_booster_view = NetworkBoosterView(caps)
        self.games_view = GamesView(caps)
        self.diag_view = DiagnosticsView(caps)
        self.settings_view = SettingsView(profile_mgr)
        self.optimizer_view = OptimizerView(caps)

        self.stack.addWidget(self.home_view)       # 0
        self.stack.addWidget(self.vitals_view)      # 1
        self.stack.addWidget(self.perf_view)        # 2
        self.stack.addWidget(self.lighting_view)    # 3
        self.stack.addWidget(self.gpu_view)         # 4
        self.stack.addWidget(self.net_booster_view) # 5
        self.stack.addWidget(self.games_view)       # 6
        self.stack.addWidget(self.diag_view)        # 7
        self.stack.addWidget(self.settings_view)    # 8
        self.stack.addWidget(self.optimizer_view)   # 9

        self.content_layout.addWidget(self.stack)
        main_layout.addWidget(content_pane)

        # Track all sidebar nav buttons for mutual exclusion
        self._all_nav_btns = []

        # Telemetry Worker
        poll_ms = profile_mgr.settings.polling_interval_ms
        self.monitor_thread = SystemMonitorThread(caps, poll_interval_ms=poll_ms, parent=self)
        self.monitor_thread.telemetry_updated.connect(self._on_telemetry_updated)
        self.monitor_thread.start()

        # Start on System Vitals
        self._select_device_tab(0)

    # ─────────────────────────────────────────────────────────────────────
    # SIDEBAR
    # ─────────────────────────────────────────────────────────────────────
    def _build_sidebar(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("sidebarFrame")

        scroll = QScrollArea(frame)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 14, 0, 12)
        layout.setSpacing(0)

        # ── NUXARCHY Brand Header ──
        brand_frame = QFrame()
        brand_frame.setStyleSheet("background: transparent; border: none; padding: 4px 16px 16px 16px;")
        b_layout = QHBoxLayout(brand_frame)
        b_layout.setContentsMargins(0, 0, 0, 0)
        b_layout.setSpacing(10)

        lbl_logo = QLabel()
        import os
        from PySide6.QtGui import QPixmap
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "nuxarchy_logo.png")
        if os.path.exists(logo_path):
            pix = QPixmap(logo_path).scaled(34, 34, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            lbl_logo.setPixmap(pix)
        b_layout.addWidget(lbl_logo)

        lbl_name = QLabel("NUXARCHY")
        lbl_name.setStyleSheet("color: #00FF85; font-size: 15px; font-weight: 900; letter-spacing: 2.5px; font-family: 'Segoe UI', sans-serif;")
        b_layout.addWidget(lbl_name)
        b_layout.addStretch()

        layout.addWidget(brand_frame)

        # ── Group 1: Main Navigation ──
        self.btn_home = self._nav_btn("⌂   HOME")
        self.btn_home.clicked.connect(lambda: self._select_global_page(_HOME, self.btn_home))
        layout.addWidget(self.btn_home)

        self.btn_perf_global = self._nav_btn("📊  PERFORMANCE")
        self.btn_perf_global.clicked.connect(lambda: self._select_device_tab(1))
        layout.addWidget(self.btn_perf_global)

        btn_ai = self._nav_btn("◇   OMEN AI")
        layout.addWidget(btn_ai)

        btn_overlays = self._nav_btn("◫   OVERLAYS")
        layout.addWidget(btn_overlays)

        layout.addWidget(self._divider())

        # ── Group 2: Games & Store ──
        btn_shop = self._nav_btn("🛍  SHOP GAMES")
        layout.addWidget(btn_shop)

        self.btn_my_games = self._nav_btn_with_badge("|||  MY GAMES", "8")
        self.btn_my_games.clicked.connect(lambda: self._select_global_page(_GAMES, self.btn_my_games))
        layout.addWidget(self.btn_my_games)

        btn_deals = self._nav_btn_with_badge("📈  DEALS", "71")
        layout.addWidget(btn_deals)

        btn_gallery = self._nav_btn_with_badge("🖼  GALLERY", "99+", arrow=True)
        layout.addWidget(btn_gallery)

        # ── OPTIMIZER (expandable) ──
        self.btn_optimizer = self._nav_btn("⏱   OPTIMIZER  ▼")
        self.btn_optimizer.clicked.connect(self._toggle_optimizer_tree)
        layout.addWidget(self.btn_optimizer)

        self.optimizer_sub_container = QWidget()
        opt_sub_layout = QVBoxLayout(self.optimizer_sub_container)
        opt_sub_layout.setContentsMargins(0, 0, 0, 0)
        opt_sub_layout.setSpacing(0)

        self.sub_quick_setup = self._sub_nav_btn("Quick Setup")
        self.sub_quick_setup.clicked.connect(lambda: self._select_optimizer_tab(0))
        opt_sub_layout.addWidget(self.sub_quick_setup)

        self.sub_booster = self._sub_nav_btn("Booster")
        self.sub_booster.clicked.connect(lambda: self._select_optimizer_tab(1))
        opt_sub_layout.addWidget(self.sub_booster)

        self.sub_cleaner = self._sub_nav_btn("Cleaner")
        self.sub_cleaner.clicked.connect(lambda: self._select_optimizer_tab(2))
        opt_sub_layout.addWidget(self.sub_cleaner)

        self.optimizer_sub_container.setVisible(False)
        layout.addWidget(self.optimizer_sub_container)

        # ── CAM & VOICE ENHANCER ──
        btn_cam = self._nav_btn("🎥  CAM & VOICE ENHANCER  ▼")
        layout.addWidget(btn_cam)

        # ── LIGHT STUDIO ──
        self.btn_ls = self._nav_btn("✨  LIGHT STUDIO")
        self.btn_ls.clicked.connect(lambda: self._select_device_tab(2))
        layout.addWidget(self.btn_ls)

        layout.addWidget(self._divider())

        # ── Group 3: OMEN 16 Device Tree ──
        self.btn_omen16 = self._nav_btn("💻  OMEN 16  ▲")
        self.btn_omen16.clicked.connect(self._toggle_device_tree)
        layout.addWidget(self.btn_omen16)

        self.device_sub_container = QWidget()
        sub_layout = QVBoxLayout(self.device_sub_container)
        sub_layout.setContentsMargins(0, 0, 0, 0)
        sub_layout.setSpacing(0)

        self.sub_vitals = self._sub_nav_btn("System Vitals", active=True)
        self.sub_vitals.clicked.connect(lambda: self._select_device_tab(0))
        sub_layout.addWidget(self.sub_vitals)

        self.sub_perf = self._sub_nav_btn("Performance Control")
        self.sub_perf.clicked.connect(lambda: self._select_device_tab(1))
        sub_layout.addWidget(self.sub_perf)

        self.sub_light = self._sub_nav_btn("Lighting")
        self.sub_light.clicked.connect(lambda: self._select_device_tab(2))
        sub_layout.addWidget(self.sub_light)

        self.sub_gpu = self._sub_nav_btn("Graphics Switcher")
        self.sub_gpu.clicked.connect(lambda: self._select_device_tab(3))
        sub_layout.addWidget(self.sub_gpu)

        self.sub_net = self._sub_nav_btn("Network Booster")
        self.sub_net.clicked.connect(lambda: self._select_device_tab(4))
        sub_layout.addWidget(self.sub_net)

        layout.addWidget(self.device_sub_container)

        layout.addWidget(self._divider())

        # ── Group 4: Help & Feedback ──
        self.btn_help = self._nav_btn("❓  HELP & FEEDBACK")
        self.btn_help.clicked.connect(lambda: self._select_global_page(_DIAG, self.btn_help))
        layout.addWidget(self.btn_help)

        layout.addStretch()

        # Version string
        lbl_ver = QLabel("1101.2609.11.0")
        lbl_ver.setStyleSheet("color: #4B5563; font-size: 10px; font-weight: 600; padding: 4px 14px;")
        layout.addWidget(lbl_ver)

        scroll.setWidget(container)

        f_layout = QVBoxLayout(frame)
        f_layout.setContentsMargins(0, 0, 0, 0)
        f_layout.addWidget(scroll)
        return frame

    # ─────────────────────────────────────────────────────────────────────
    # TOP TAB BAR
    # ─────────────────────────────────────────────────────────────────────
    def _build_top_tab_bar(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("topNavTabs")

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(4)

        self.top_tab_buttons = []
        tabs = [
            ("System Vitals", 0),
            ("Performance Control", 1),
            ("Lighting", 2),
            ("Graphics Switcher", 3),
            ("Network Booster", 4),
        ]

        for text, idx in tabs:
            btn = QPushButton(text)
            btn.setProperty("class", "topTabBtn")
            btn.clicked.connect(lambda checked, i=idx: self._select_device_tab(i))
            self.top_tab_buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()
        return frame

    # ─────────────────────────────────────────────────────────────────────
    # NAVIGATION LOGIC
    # ─────────────────────────────────────────────────────────────────────
    def _select_device_tab(self, tab_idx: int):
        """Switches device tab (0: Vitals, 1: Perf, 2: Light, 3: GPU, 4: Net)."""
        self.top_tabs.setVisible(True)

        # Clear all sidebar active states
        self._clear_all_nav_active()

        # Update top tab buttons active styles
        for i, btn in enumerate(self.top_tab_buttons):
            if i == tab_idx:
                btn.setProperty("class", "topTabBtn topTabBtnActive")
            else:
                btn.setProperty("class", "topTabBtn")
            btn.style().unpolish(btn); btn.style().polish(btn)

        # Update sidebar sub-item active styles
        sub_items = [self.sub_vitals, self.sub_perf, self.sub_light, self.sub_gpu, self.sub_net]
        for i, item in enumerate(sub_items):
            if i == tab_idx:
                item.setProperty("class", "subNavItem subNavItemActive")
            else:
                item.setProperty("class", "subNavItem")
            item.style().unpolish(item); item.style().polish(item)

        # Clear optimizer sub-item highlights
        for item in [self.sub_quick_setup, self.sub_booster, self.sub_cleaner]:
            item.setProperty("class", "subNavItem")
            item.style().unpolish(item); item.style().polish(item)

        self.stack.setCurrentIndex(tab_idx + 1)

    def _select_global_page(self, stack_idx: int, nav_btn):
        """Switches to a non-device page (e.g. HOME, MY GAMES)."""
        self.top_tabs.setVisible(False)

        # Clear all sidebar active states
        self._clear_all_nav_active()

        # Highlight clicked button
        if isinstance(nav_btn, QPushButton):
            nav_btn.setProperty("class", "sideNavBtn sideNavBtnActive")
            nav_btn.style().unpolish(nav_btn); nav_btn.style().polish(nav_btn)

        self.stack.setCurrentIndex(stack_idx)

    def _select_optimizer_tab(self, sub_idx: int):
        """Switch to Optimizer view and select sub-tab."""
        self.top_tabs.setVisible(False)

        # Clear all sidebar active states
        self._clear_all_nav_active()

        # Highlight the Optimizer parent
        self.btn_optimizer.setProperty("class", "sideNavBtn sideNavBtnActive")
        self.btn_optimizer.style().unpolish(self.btn_optimizer)
        self.btn_optimizer.style().polish(self.btn_optimizer)

        # Highlight sub-items
        opt_subs = [self.sub_quick_setup, self.sub_booster, self.sub_cleaner]
        for i, item in enumerate(opt_subs):
            if i == sub_idx:
                item.setProperty("class", "subNavItem subNavItemActive")
            else:
                item.setProperty("class", "subNavItem")
            item.style().unpolish(item); item.style().polish(item)

        self.stack.setCurrentIndex(_OPTIMIZER)
        self.optimizer_view._select_sub_tab(sub_idx)

    def _clear_all_nav_active(self):
        """Reset all nav buttons to inactive state."""
        for btn in [self.btn_home, self.btn_perf_global, self.btn_optimizer]:
            btn.setProperty("class", "sideNavBtn")
            btn.style().unpolish(btn); btn.style().polish(btn)

        # Clear device sub-items
        for item in [self.sub_vitals, self.sub_perf, self.sub_light, self.sub_gpu, self.sub_net]:
            item.setProperty("class", "subNavItem")
            item.style().unpolish(item); item.style().polish(item)

        # Clear optimizer sub-items
        for item in [self.sub_quick_setup, self.sub_booster, self.sub_cleaner]:
            item.setProperty("class", "subNavItem")
            item.style().unpolish(item); item.style().polish(item)

    # ─────────────────────────────────────────────────────────────────────
    # TREE TOGGLES
    # ─────────────────────────────────────────────────────────────────────
    def _toggle_device_tree(self):
        vis = not self.device_sub_container.isVisible()
        self.device_sub_container.setVisible(vis)
        self.btn_omen16.setText("💻  OMEN 16  ▲" if vis else "💻  OMEN 16  ▼")

    def _toggle_optimizer_tree(self):
        vis = not self.optimizer_sub_container.isVisible()
        self.optimizer_sub_container.setVisible(vis)
        self.btn_optimizer.setText("⏱   OPTIMIZER  ▲" if vis else "⏱   OPTIMIZER  ▼")
        if vis:
            # Auto-select Quick Setup when expanding
            self._select_optimizer_tab(0)

    # ─────────────────────────────────────────────────────────────────────
    # WIDGET FACTORY HELPERS
    # ─────────────────────────────────────────────────────────────────────
    def _nav_btn(self, text: str, active: bool = False) -> QPushButton:
        btn = QPushButton(text)
        btn.setProperty("class", "sideNavBtn sideNavBtnActive" if active else "sideNavBtn")
        return btn

    def _sub_nav_btn(self, text: str, active: bool = False) -> QPushButton:
        btn = QPushButton(text)
        btn.setProperty("class", "subNavItem subNavItemActive" if active else "subNavItem")
        return btn

    def _nav_btn_with_badge(self, text: str, badge_val: str, arrow: bool = False) -> QFrame:
        box = QFrame()
        box.setStyleSheet("background: transparent; border: none;")
        l = QHBoxLayout(box)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(4)

        btn = QPushButton(text)
        btn.setProperty("class", "sideNavBtn")
        l.addWidget(btn, 1)

        badge = QLabel(badge_val)
        badge.setProperty("class", "navPill")
        badge.setAlignment(Qt.AlignCenter)
        l.addWidget(badge)

        if arrow:
            arr = QLabel("▼")
            arr.setStyleSheet("color: #6B7280; font-size: 9px; margin-right: 6px;")
            l.addWidget(arr)

        box.clicked = btn.clicked
        return box

    def _divider(self) -> QFrame:
        div = QFrame()
        div.setStyleSheet("border-top: 1px solid #181A22; margin: 6px 10px;")
        div.setFixedHeight(1)
        return div

    # ─────────────────────────────────────────────────────────────────────
    # TELEMETRY
    # ─────────────────────────────────────────────────────────────────────
    def _on_telemetry_updated(self, snap: SystemSnapshot):
        curr = self.stack.currentIndex()
        if curr == _HOME:
            self.home_view.update_telemetry(snap)
        elif curr == _VITALS:
            self.vitals_view.update_telemetry(snap)
        elif curr == _PERF:
            self.perf_view.update_telemetry(snap)
        elif curr == _NET_BOOSTER:
            self.net_booster_view.update_telemetry(snap)

    def closeEvent(self, event):
        if hasattr(self, "monitor_thread") and self.monitor_thread.isRunning():
            self.monitor_thread.stop()
        event.accept()
