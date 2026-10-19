"""
Custom Telemetry Gauge Card Widget
Displays telemetry metrics with title, value, unit, progress indicator, and status badge.
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt


class GaugeCard(QFrame):
    def __init__(self, title: str, unit: str = "%", max_value: float = 100.0, parent=None):
        super().__init__(parent)
        self.setObjectName("gaugeCard")
        self.setProperty("class", "cardFrame")
        self.unit = unit
        self.max_value = max_value

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        # Top row: Title and Status Badge
        top_row = QHBoxLayout()
        self.title_label = QLabel(title.upper())
        self.title_label.setProperty("class", "cardTitle")
        top_row.addWidget(self.title_label)

        top_row.addStretch()

        self.badge_label = QLabel("NORMAL")
        self.badge_label.setProperty("class", "badge badgeSuccess")
        top_row.addWidget(self.badge_label)
        layout.addLayout(top_row)

        # Middle row: Main Value and Unit
        val_row = QHBoxLayout()
        val_row.setSpacing(4)
        self.value_label = QLabel("0")
        self.value_label.setProperty("class", "cardValue")
        val_row.addWidget(self.value_label)

        self.unit_label = QLabel(unit)
        self.unit_label.setProperty("class", "cardUnit")
        self.unit_label.setAlignment(Qt.AlignBottom)
        self.unit_label.setContentsMargins(0, 0, 0, 4)
        val_row.addWidget(self.unit_label)

        val_row.addStretch()
        layout.addLayout(val_row)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Subtext / Secondary details
        self.subtext_label = QLabel("--")
        self.subtext_label.setProperty("class", "cardSubtext")
        layout.addWidget(self.subtext_label)

    def update_value(self, value: float, subtext: str = "", badge_text: str = None, badge_type: str = "badgeSuccess"):
        if value is None:
            self.value_label.setText("--")
            self.progress_bar.setValue(0)
            self.badge_label.setText("N/A")
            self.badge_label.setProperty("class", "badge badgeWarning")
            return

        # Format number
        if isinstance(value, float):
            self.value_label.setText(f"{value:.1f}" if value < 100 else f"{int(value)}")
        else:
            self.value_label.setText(str(value))

        pct = int((value / self.max_value) * 100) if self.max_value > 0 else 0
        self.progress_bar.setValue(max(0, min(100, pct)))

        if subtext:
            self.subtext_label.setText(subtext)

        if badge_text:
            self.badge_label.setText(badge_text)
            self.badge_label.setProperty("class", f"badge {badge_type}")
            self.badge_label.style().unpolish(self.badge_label)
            self.badge_label.style().polish(self.badge_label)
