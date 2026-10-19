"""
Generate high-resolution PNG snapshots of the Optimizer sub-views (Quick Setup, Booster, Cleaner)
and the main window.
"""
import sys
import os

root_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, root_dir)

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from backend.capability import CapabilityDetector
from services.profile_manager import ProfileManager
from app.ui.main_window import MainWindow

app = QApplication.instance() or QApplication(sys.argv)
app.setFont(QFont("Segoe UI", 9))

style_path = os.path.join(root_dir, "app", "style.qss")
if os.path.exists(style_path):
    with open(style_path, "r", encoding="utf-8") as f:
        app.setStyleSheet(f.read())

detector = CapabilityDetector(simulation_mode=True)
caps = detector.detect()
profile_mgr = ProfileManager(config_dir=os.path.join(root_dir, "tests", "temp_config"))

window = MainWindow(caps, profile_mgr)
window.resize(1280, 800)
window.show()

tests_dir = os.path.join(root_dir, "tests")
os.makedirs(tests_dir, exist_ok=True)

# 1. Capture Quick Setup
window._select_optimizer_tab(0)
app.processEvents()
pix_quick = window.grab()
pix_quick.save(os.path.join(tests_dir, "snapshot_quick_setup.png"))

# 2. Capture Booster
window._select_optimizer_tab(1)
app.processEvents()
pix_booster = window.grab()
pix_booster.save(os.path.join(tests_dir, "snapshot_booster.png"))

# 3. Capture Cleaner
window._select_optimizer_tab(2)
app.processEvents()
pix_cleaner = window.grab()
pix_cleaner.save(os.path.join(tests_dir, "snapshot_cleaner.png"))

print("Snapshots saved successfully!")
window.close()
