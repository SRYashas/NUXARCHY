"""
NUXARCHY Hardware Center: Optimizer View Container
Wraps the three Optimizer sub-tabs (Quick Setup, Booster, Cleaner)
with top navigation tabs.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QStackedWidget
)
from PySide6.QtCore import Qt

from nuxarchy.backend.capability import HardwareCapabilities
from nuxarchy.ui.views.optimizer_quick_setup_view import OptimizerQuickSetupView
from nuxarchy.ui.views.optimizer_booster_view import OptimizerBoosterView
from nuxarchy.ui.views.optimizer_cleaner_view import OptimizerCleanerView


class OptimizerView(QWidget):
    """Container view with Quick Setup / Booster / Cleaner sub-tabs."""

    def __init__(self, caps: HardwareCapabilities, parent=None):
        super().__init__(parent)
        self.caps = caps

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sub-tab bar matching Screenshots 1, 2, 3
        tab_bar = QFrame()
        tab_bar.setObjectName("optimizerTabBar")
        tab_bar.setStyleSheet("""
            QFrame#optimizerTabBar {
                background-color: #0E1015;
                border-bottom: 1px solid #1C202B;
                min-height: 44px;
                max-height: 44px;
            }
        """)

        tb_layout = QHBoxLayout(tab_bar)
        tb_layout.setContentsMargins(24, 0, 24, 0)
        tb_layout.setSpacing(6)

        self.sub_tabs = []
        tab_labels = ["Quick Setup", "Booster", "Cleaner"]

        for i, text in enumerate(tab_labels):
            btn = QPushButton(text)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, idx=i: self._select_sub_tab(idx))
            self.sub_tabs.append(btn)
            tb_layout.addWidget(btn)

        tb_layout.addStretch()
        layout.addWidget(tab_bar)

        # Stacked views
        self.stack = QStackedWidget()
        self.quick_setup_view = OptimizerQuickSetupView(caps)
        self.booster_view = OptimizerBoosterView(caps)
        self.cleaner_view = OptimizerCleanerView(caps)

        # Connect inter-view navigation signals
        self.quick_setup_view.request_tab_switch.connect(self._select_sub_tab)

        self.stack.addWidget(self.quick_setup_view)
        self.stack.addWidget(self.booster_view)
        self.stack.addWidget(self.cleaner_view)

        layout.addWidget(self.stack)

        # Default to Quick Setup
        self._select_sub_tab(0)

    def _select_sub_tab(self, idx: int):
        self.stack.setCurrentIndex(idx)
        for i, btn in enumerate(self.sub_tabs):
            if i == idx:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #21242D;
                        color: #FFFFFF;
                        font-size: 12px;
                        font-weight: 800;
                        padding: 10px 24px;
                        border: 1px solid #232734;
                        border-top: 3px solid #E02874;
                        border-radius: 4px 4px 0 0;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #13151D;
                        color: #8E95A5;
                        font-size: 12px;
                        font-weight: 700;
                        padding: 10px 24px;
                        border: 1px solid #20232E;
                        border-top: 3px solid transparent;
                        border-radius: 4px 4px 0 0;
                    }
                    QPushButton:hover {
                        color: #FFFFFF;
                        background-color: #191C25;
                        border-color: #2D3342;
                    }
                """)
