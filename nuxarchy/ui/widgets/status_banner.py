"""
Status Banner Widget
Displays hardware detection status, active drivers, and capability summary.
"""

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout
from nuxarchy.backend.capability import HardwareCapabilities


class StatusBanner(QFrame):
    def __init__(self, caps: HardwareCapabilities, parent=None):
        super().__init__(parent)
        self.setObjectName("statusBanner")
        self.setStyleSheet("""
            QFrame#statusBanner {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(0, 255, 209, 0.1), stop:1 rgba(157, 78, 221, 0.08));
                border: 1px solid rgba(0, 255, 209, 0.25);
                border-radius: 10px;
                padding: 10px 16px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)

        # Status icon / dot
        dot = QLabel("●")
        dot.setStyleSheet("color: #00FFD1; font-size: 14px;")
        layout.addWidget(dot)

        # Content
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        title = QLabel(f"{caps.product_name} • {caps.system_vendor}")
        title.setStyleSheet("color: #FFFFFF; font-weight: 800; font-size: 13px; letter-spacing: 0.5px;")
        text_layout.addWidget(title)

        sub = QLabel(f"BaseBoard {caps.board_name or 'N/A'} | BIOS {caps.bios_version or 'N/A'} | {caps.cpu_model} | {caps.discrete_gpu_name}")
        sub.setStyleSheet("color: #9CA3AF; font-size: 11px;")
        text_layout.addWidget(sub)

        layout.addLayout(text_layout)
        layout.addStretch()

        # Capability pill
        pill = QLabel("NUXARCHY NATIVE")
        pill.setStyleSheet("""
            background-color: rgba(0, 255, 209, 0.15);
            color: #00FFD1;
            font-size: 10px;
            font-weight: 800;
            padding: 4px 10px;
            border-radius: 4px;
            border: 1px solid rgba(0, 255, 209, 0.3);
            letter-spacing: 1px;
        """)
        layout.addWidget(pill)
