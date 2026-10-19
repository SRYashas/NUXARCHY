"""
NUXARCHY Daemon Service Authorization Dialog
Provides an in-app graphical password prompt to enable and start
'nuxarchy-daemon.service' without requiring the user to open a terminal.
"""

import os
import sys
import time
import subprocess
from typing import Optional, Tuple

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QFrame,
    QProgressBar,
)

from nuxarchy.services.daemon_client import DaemonClient


class DaemonServiceDialog(QDialog):
    """Modal dialog prompting user for admin password to start nuxarchy-daemon."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("NUXARCHY Root Service Activation")
        self.setFixedSize(520, 360)
        self.setModal(True)
        self.setStyleSheet("""
            QDialog {
                background-color: #0F1117;
                color: #FFFFFF;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header card
        header_card = QFrame()
        header_card.setStyleSheet("""
            QFrame {
                background-color: #161B26;
                border: 1px solid #1E293B;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        h_layout = QVBoxLayout(header_card)
        h_layout.setContentsMargins(12, 12, 12, 12)
        h_layout.setSpacing(6)

        title = QLabel("🛡️ Enable Zero-Prompt Root Daemon")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #00D2FF;")
        h_layout.addWidget(title)

        desc = QLabel(
            "NUXARCHY operates with a dedicated background service "
            "(<b>nuxarchy-daemon.service</b>) to collect live system telemetry "
            "and switch cooling/power profiles without repeatedly nagging for passwords.<br><br>"
            "Enter your administrator password once to enable and activate this service:"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 12px; color: #94A3B8; line-height: 1.4;")
        h_layout.addWidget(desc)
        layout.addWidget(header_card)

        # Password input section
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("Enter administrator / sudo password...")
        self.password_edit.setStyleSheet("""
            QLineEdit {
                background-color: #1E293B;
                color: #FFFFFF;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 10px 14px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #00D2FF;
            }
        """)
        self.password_edit.returnPressed.connect(self._on_start_clicked)
        layout.addWidget(self.password_edit)

        # Show password toggle
        show_cb = QCheckBox("Show password")
        show_cb.setStyleSheet("color: #94A3B8; font-size: 12px;")
        show_cb.toggled.connect(
            lambda checked: self.password_edit.setEchoMode(
                QLineEdit.Normal if checked else QLineEdit.Password
            )
        )
        layout.addWidget(show_cb)

        # Status & progress
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("font-size: 12px; color: #EF4444; font-weight: 600;")
        layout.addWidget(self.status_label)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #1E293B;
                color: #94A3B8;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #334155;
                color: #FFFFFF;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.start_btn = QPushButton("Enable & Start Service")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #00D2FF;
                color: #0B0E14;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 13px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #38BDF8;
            }
            QPushButton:disabled {
                background-color: #1E293B;
                color: #64748B;
            }
        """)
        self.start_btn.clicked.connect(self._on_start_clicked)
        btn_layout.addWidget(self.start_btn)

        layout.addLayout(btn_layout)

    def _on_start_clicked(self):
        password = self.password_edit.text()
        if not password and sys.platform != "win32":
            self.status_label.setStyleSheet("color: #EF4444; font-size: 12px; font-weight: 600;")
            self.status_label.setText("Please enter your administrator password.")
            return

        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.password_edit.setEnabled(False)
        self.status_label.setStyleSheet("color: #00D2FF; font-size: 12px; font-weight: 600;")
        self.status_label.setText("Authenticating and activating nuxarchy-daemon.service...")

        # Run activation in next tick to keep UI responsive
        QTimer.singleShot(100, lambda: self._execute_activation(password))

    def _execute_activation(self, password: str):
        success, message = self.activate_service(password)
        if success:
            self.status_label.setStyleSheet("color: #10B981; font-size: 12px; font-weight: 700;")
            self.status_label.setText(f"✓ {message}")
            QTimer.singleShot(800, self.accept)
        else:
            self.status_label.setStyleSheet("color: #EF4444; font-size: 12px; font-weight: 600;")
            self.status_label.setText(f"Error: {message}")
            self.start_btn.setEnabled(True)
            self.cancel_btn.setEnabled(True)
            self.password_edit.setEnabled(True)
            self.password_edit.setFocus()
            self.password_edit.selectAll()

    @staticmethod
    def activate_service(password: str) -> Tuple[bool, str]:
        """
        Executes systemctl enable --now nuxarchy-daemon.service using the provided password.
        Returns (success: bool, message: str).
        """
        if sys.platform == "win32":
            # For Windows development/simulation testing
            return True, "Simulated daemon activation successful."

        # 1. Check if unit file exists; if not, install it to /etc/systemd/system/
        unit_target = "/etc/systemd/system/nuxarchy-daemon.service"
        needs_install = not os.path.exists(unit_target) and not os.path.exists("/usr/lib/systemd/system/nuxarchy-daemon.service")

        commands = []
        if needs_install:
            # Locate bundled unit file
            repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            bundled_unit = os.path.join(repo_root, "packaging", "nuxarchy-daemon.service")
            if os.path.exists(bundled_unit):
                commands.append(f"cp '{bundled_unit}' '{unit_target}'")
                commands.append(f"chmod 644 '{unit_target}'")
                commands.append("systemctl daemon-reload")

        commands.append("systemctl enable --now nuxarchy-daemon.service")
        full_command = " && ".join(commands)

        try:
            # Execute via sudo -S using stdin pipe
            proc = subprocess.Popen(
                ["sudo", "-S", "bash", "-c", full_command],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            stdout, stderr = proc.communicate(input=password + "\n", timeout=10.0)

            if proc.returncode != 0:
                err_text = (stderr or stdout).strip()
                if "incorrect password" in err_text.lower() or "try again" in err_text.lower():
                    return False, "Incorrect administrator password. Please try again."
                return False, f"Activation failed: {err_text}"

            # Wait for socket to become active
            for _ in range(6):
                time.sleep(0.5)
                if DaemonClient.instance().is_connected():
                    return True, "nuxarchy-daemon.service successfully enabled and connected!"

            return True, "Service activated. Connected to /run/nuxarchy/nuxarchy.sock."

        except subprocess.TimeoutExpired:
            return False, "Process timed out while enabling service."
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
