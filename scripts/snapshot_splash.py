"""
Capture snapshot of the NUXARCHY Loading Splash Screen.
"""
import sys
import os

root_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, root_dir)

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from nuxarchy.ui.splash_screen import SplashScreen

app = QApplication.instance() or QApplication(sys.argv)
app.setFont(QFont("Segoe UI", 9))

splash = SplashScreen()
splash.opacity_effect.setOpacity(1.0)
splash.progress.setValue(70)
splash.lbl_status.setText("LOADING LIGHTING & THERMAL PROFILES...")
splash.show()
app.processEvents()

pix = splash.grab()
save_path = os.path.join(root_dir, "tests", "snapshot_splash_screen.png")
pix.save(save_path)
print(f"Splash screen saved to {save_path}")
splash.close()
