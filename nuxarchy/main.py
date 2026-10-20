"""
NUXARCHY Unprivileged GUI Entrypoint
Initializes PyQt6 application, applies OMEN dark theme QSS stylesheet,
configures application icon and window properties, and presents MainWindow.
"""

import sys
import os
import argparse

# Ensure workspace root in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

from nuxarchy.ui.main_window import MainWindow
from nuxarchy import __version__


def main():
    parser = argparse.ArgumentParser(description="NUXARCHY: Linux-Native Gaming Hub")
    parser.add_argument("--minimized", action="store_true", help="Start application minimized to tray/background")
    parser.add_argument("--version", action="version", version=f"NUXARCHY {__version__}")
    args, unknown = parser.parse_known_args()

    # Headless session warning on Linux
    if sys.platform != "win32" and not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
        print("[!] Warning: Neither DISPLAY nor WAYLAND_DISPLAY environment variables are set.", file=sys.stderr)
        print("[!] Ensure an active X11 or Wayland desktop session is available.", file=sys.stderr)

    try:
        app = QApplication(sys.argv)
    except Exception as e:
        print(f"[!] Error: Could not initialize Qt GUI application: {e}", file=sys.stderr)
        sys.exit(1)

    app.setApplicationName("NUXARCHY")
    app.setOrganizationName("Nuxarchy")

    # Load stylesheet
    style_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "style.qss")
    if os.path.exists(style_path):
        try:
            with open(style_path, "r", encoding="utf-8") as f:
                app.setStyleSheet(f.read())
        except Exception as e:
            print(f"[!] Warning: Could not load stylesheet: {e}", file=sys.stderr)

    # Window Icon
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "nuxarchy_logo.png")
    if os.path.exists(logo_path):
        app.setWindowIcon(QIcon(logo_path))

    window = MainWindow()
    if not args.minimized:
        window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
