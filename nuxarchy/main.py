"""
NUXARCHY: Universal Native Linux & Cross-Platform Hardware Control Center
Main Entry Point with Cyberpunk Loading Splash Screen & Logo Integration
"""

import sys
import os
import argparse

# Add workspace root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from nuxarchy.backend.capability import CapabilityDetector
from nuxarchy.services.profile_manager import ProfileManager
from nuxarchy.ui.main_window import MainWindow
from nuxarchy.ui.splash_screen import SplashScreen


def main():
    parser = argparse.ArgumentParser(description="NUXARCHY: Arch Linux Control Center")
    parser.add_argument("--simulated", action="store_true", help="Force simulated hardware mode for development/testing")
    parser.add_argument("--minimized", action="store_true", help="Start application minimized")
    parser.add_argument("--no-splash", action="store_true", help="Skip loading splash screen")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setApplicationName("NUXARCHY")
    app.setOrganizationName("Nuxarchy")

    # Set Application Window Icon
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "nuxarchy_logo.png")
    if os.path.exists(logo_path):
        app.setWindowIcon(QIcon(logo_path))

    # Load stylesheet
    style_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "style.qss")
    if os.path.exists(style_path):
        with open(style_path, "r", encoding="utf-8") as f:
            qss = f.read()
            res_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources").replace("\\", "/")
            qss = qss.replace("nuxarchy/resources", res_dir).replace("app/resources", res_dir)
            app.setStyleSheet(qss)

    # Detect hardware capabilities
    detector = CapabilityDetector(simulation_mode=args.simulated)
    caps = detector.detect()

    # Load settings
    profile_mgr = ProfileManager()

    # Create main window
    window = MainWindow(caps, profile_mgr)

    if args.minimized or profile_mgr.settings.start_minimized:
        pass
    elif args.no_splash:
        window.show()
    else:
        # Show Black Splash Screen with NUXARCHY Logo & Title
        splash = SplashScreen()
        splash.finished.connect(window.show)
        splash.start_loading()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
