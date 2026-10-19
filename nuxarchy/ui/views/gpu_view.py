"""
OMEN Gaming Hub: Graphics Switcher View (Pixel-Perfect Recreation)
Matches Screenshot 4:
"Select a GPU mode" with large Hybrid (Active glowing border) and Discrete cards,
and bottom "RESET TO DEFAULT" button.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt

from nuxarchy.backend.capability import HardwareCapabilities
from nuxarchy.backend.telemetry.system_monitor import SystemSnapshot


class GpuView(QWidget):
    def __init__(self, caps: HardwareCapabilities, parent=None):
        super().__init__(parent)
        self.caps = caps
        self.current_mode = "hybrid"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 30)
        layout.setSpacing(28)

        # 1. Centered Title
        title = QLabel("Select a GPU mode")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #FFFFFF; font-size: 18px; font-weight: 800; letter-spacing: 0.5px;")
        layout.addWidget(title)

        # 2. Centered Cards Container
        cards_container = QHBoxLayout()
        cards_container.setAlignment(Qt.AlignCenter)
        cards_container.setSpacing(24)

        # Hybrid Card (Active in Screenshot 4 with glowing pink/orange gradient border)
        self.card_hybrid = QFrame()
        self.card_hybrid.setFixedSize(280, 200)
        self.card_hybrid.setCursor(Qt.PointingHandCursor)
        h_layout = QVBoxLayout(self.card_hybrid)
        h_layout.setAlignment(Qt.AlignCenter)
        h_layout.setSpacing(10)

        icon_h = QLabel("🌱")
        icon_h.setAlignment(Qt.AlignCenter)
        icon_h.setStyleSheet("font-size: 32px;")
        h_layout.addWidget(icon_h)

        lbl_h_title = QLabel("Hybrid")
        lbl_h_title.setAlignment(Qt.AlignCenter)
        lbl_h_title.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: 800;")
        h_layout.addWidget(lbl_h_title)

        lbl_h_desc = QLabel("Uses both integrated and discrete graphics depending on the application.")
        lbl_h_desc.setAlignment(Qt.AlignCenter)
        lbl_h_desc.setWordWrap(True)
        lbl_h_desc.setStyleSheet("color: #9CA3AF; font-size: 11px; line-height: 1.4; padding: 0 10px;")
        h_layout.addWidget(lbl_h_desc)

        self.card_hybrid.mousePressEvent = lambda e: self._select_gpu_mode("hybrid")
        cards_container.addWidget(self.card_hybrid)

        # Discrete Card
        self.card_discrete = QFrame()
        self.card_discrete.setFixedSize(280, 200)
        self.card_discrete.setCursor(Qt.PointingHandCursor)
        d_layout = QVBoxLayout(self.card_discrete)
        d_layout.setAlignment(Qt.AlignCenter)
        d_layout.setSpacing(10)

        icon_d = QLabel("🖥️")
        icon_d.setAlignment(Qt.AlignCenter)
        icon_d.setStyleSheet("font-size: 32px;")
        d_layout.addWidget(icon_d)

        lbl_d_title = QLabel("Discrete")
        lbl_d_title.setAlignment(Qt.AlignCenter)
        lbl_d_title.setStyleSheet("color: #9CA3AF; font-size: 16px; font-weight: 800;")
        d_layout.addWidget(lbl_d_title)

        lbl_d_desc = QLabel("Suitable for gaming and graphics intensive apps. Might increase heat and noise levels.")
        lbl_d_desc.setAlignment(Qt.AlignCenter)
        lbl_d_desc.setWordWrap(True)
        lbl_d_desc.setStyleSheet("color: #6B7280; font-size: 11px; line-height: 1.4; padding: 0 10px;")
        d_layout.addWidget(lbl_d_desc)

        self.card_discrete.mousePressEvent = lambda e: self._select_gpu_mode("discrete")
        cards_container.addWidget(self.card_discrete)

        layout.addLayout(cards_container)
        layout.addStretch()

        # 3. Bottom Reset Button
        btn_reset = QPushButton("RESET TO DEFAULT")
        btn_reset.setStyleSheet("""
            QPushButton {
                background-color: #12141A;
                color: #FFFFFF;
                border: 1px solid #282D3D;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 11px;
                font-weight: 800;
                letter-spacing: 0.5px;
                max-width: 140px;
            }
            QPushButton:hover {
                border: 1px solid #3E455E;
                background-color: #1A1D27;
            }
        """)
        btn_reset.clicked.connect(lambda: self._select_gpu_mode("hybrid"))
        layout.addWidget(btn_reset)

        self._refresh_styles()

    def _select_gpu_mode(self, mode: str):
        self.current_mode = mode
        self._refresh_styles()
        if mode == "discrete":
            QMessageBox.information(
                self,
                "GPU Switcher",
                "Switching physical MUX to Discrete Mode requires writing to UEFI NVRAM and restarting the laptop.\n\n"
                "In Linux / Wayland, Hybrid mode with NVIDIA PRIME offload (prime-run) is actively active and recommended."
            )

    def _refresh_styles(self):
        if self.current_mode == "hybrid":
            self.card_hybrid.setStyleSheet("""
                QFrame {
                    background-color: #161822;
                    border: 2px solid #FF2A54;
                    border-radius: 8px;
                }
            """)
            self.card_discrete.setStyleSheet("""
                QFrame {
                    background-color: #12141A;
                    border: 1px solid #1E222D;
                    border-radius: 8px;
                }
                QFrame:hover {
                    border: 1px solid #30374A;
                }
            """)
        else:
            self.card_discrete.setStyleSheet("""
                QFrame {
                    background-color: #161822;
                    border: 2px solid #FF2A54;
                    border-radius: 8px;
                }
            """)
            self.card_hybrid.setStyleSheet("""
                QFrame {
                    background-color: #12141A;
                    border: 1px solid #1E222D;
                    border-radius: 8px;
                }
                QFrame:hover {
                    border: 1px solid #30374A;
                }
            """)

    def update_telemetry(self, snap: SystemSnapshot):
        pass
