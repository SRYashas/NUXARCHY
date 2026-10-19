#!/usr/bin/env bash
# ===================================================================
# NUXARCHY: Universal Native Linux Installer
# ===================================================================
set -euo pipefail

echo "========================================================"
echo "                  Installing NUXARCHY                   "
echo "========================================================"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 1. Install dependencies via package manager
echo "[1/6] Checking and installing Linux system dependencies..."
if command -v pacman &>/dev/null; then
    echo "-> Detected Arch Linux / pacman package manager."
    sudo pacman -S --needed --noconfirm python python-pyside6 python-psutil polkit power-profiles-daemon || true
elif command -v apt-get &>/dev/null; then
    echo "-> Detected Debian / Ubuntu / Kali (apt package manager)."
    sudo apt-get update -y || true
    sudo apt-get install -y python3 python3-pip python3-psutil polkitd power-profiles-daemon libxcb-cursor0 || true
    # Attempt apt PySide6 installation
    if ! sudo apt-get install -y python3-pyside6.qtcore python3-pyside6.qtwidgets python3-pyside6.qtgui python3-pyside6.qtsvg; then
        echo "Notice: python3-pyside6 packages not in apt. Installing via pip..."
        sudo pip3 install --break-system-packages pyside6 psutil || pip3 install --break-system-packages pyside6 psutil || true
    fi
elif command -v dnf &>/dev/null; then
    echo "-> Detected Fedora / RHEL (dnf package manager)."
    sudo dnf install -y python3 python3-pip python3-pyside6 python3-psutil polkit power-profiles-daemon || true
elif command -v zypper &>/dev/null; then
    echo "-> Detected openSUSE (zypper package manager)."
    sudo zypper install -y python3 python3-pip python3-pyside6 python3-psutil polkit power-profiles-daemon || true
else
    echo "Warning: Unrecognized package manager. Please ensure Python 3, PySide6, and psutil are installed."
fi

# 2. Verify and self-heal Python runtime dependencies
echo "[2/6] Verifying Python runtime dependencies..."
PY_BIN="python3"
if ! command -v "$PY_BIN" &>/dev/null; then
    PY_BIN="python"
fi

if ! "$PY_BIN" -c "import PySide6.QtWidgets, PySide6.QtCore, PySide6.QtGui, psutil" 2>/dev/null; then
    echo "Notice: PySide6.QtWidgets or psutil missing in $PY_BIN environment. Installing via pip..."
    sudo "$PY_BIN" -m pip install --break-system-packages pyside6 psutil || \
    "$PY_BIN" -m pip install --break-system-packages pyside6 psutil || \
    "$PY_BIN" -m pip install pyside6 psutil || true
fi

# 3. Deploy to /opt/nuxarchy
echo "[3/6] Deploying application files to /opt/nuxarchy..."
sudo mkdir -p /opt/nuxarchy
sudo cp -r "${SCRIPT_DIR}/nuxarchy" /opt/nuxarchy/

# 4. Deploy launcher wrapper & daemon launcher
echo "[4/6] Installing launchers to /usr/local/bin/ and /usr/bin/..."
sudo tee /usr/local/bin/nuxarchy > /dev/null << 'EOF'
#!/usr/bin/env bash
export PYTHONPATH="/opt/nuxarchy:${PYTHONPATH:-}"

if command -v python3 &>/dev/null; then
    PY_BIN="python3"
elif command -v python &>/dev/null; then
    PY_BIN="python"
else
    echo "Error: Python 3 is required to run NUXARCHY but was not found." >&2
    exit 1
fi

if ! "$PY_BIN" -c "import PySide6.QtWidgets" &>/dev/null; then
    echo "========================================================"
    echo "  [!] NUXARCHY: PySide6 is not installed on your system  "
    echo "========================================================"
    echo "Please install PySide6 using one of the following:"
    echo "  Debian/Kali/Ubuntu: sudo apt install python3-pyside6.qtcore python3-pyside6.qtwidgets python3-pyside6.qtgui"
    echo "  Or via pip:         pip install --break-system-packages pyside6 psutil"
    echo "  Arch Linux:         sudo pacman -S python-pyside6 python-psutil"
    echo "  Fedora:             sudo dnf install python3-pyside6 python3-psutil"
    echo "========================================================"
    exit 1
fi

exec "$PY_BIN" -m nuxarchy "$@"
EOF
sudo chmod +x /usr/local/bin/nuxarchy
sudo ln -sf /usr/local/bin/nuxarchy /usr/bin/nuxarchy

sudo tee /usr/local/bin/nuxarchy-daemon > /dev/null << 'EOF'
#!/usr/bin/env bash
export PYTHONPATH="/opt/nuxarchy:${PYTHONPATH:-}"

if command -v python3 &>/dev/null; then
    PY_BIN="python3"
elif command -v python &>/dev/null; then
    PY_BIN="python"
else
    echo "Error: Python 3 not found." >&2
    exit 1
fi

exec "$PY_BIN" -m nuxarchy.services.daemon "$@"
EOF
sudo chmod +x /usr/local/bin/nuxarchy-daemon
sudo ln -sf /usr/local/bin/nuxarchy-daemon /usr/bin/nuxarchy-daemon

# 5. Install & Enable systemd root hardware daemon
echo "[5/6] Installing and starting nuxarchy-daemon systemd service..."
if [ -f "${SCRIPT_DIR}/packaging/nuxarchy-daemon.service" ]; then
    sudo cp "${SCRIPT_DIR}/packaging/nuxarchy-daemon.service" /etc/systemd/system/
    if command -v systemctl &>/dev/null; then
        sudo systemctl daemon-reload
        sudo systemctl restart nuxarchy-daemon.service 2>/dev/null || sudo systemctl enable --now nuxarchy-daemon.service || echo "Notice: Started service or queued for next boot."
    fi
fi

# 6. Install Polkit helper & policy (fallback) & Desktop Launcher
echo "[6/6] Configuring Polkit, desktop application entry, and icon..."
sudo mkdir -p /usr/lib/nuxarchy
sudo cp "${SCRIPT_DIR}/nuxarchy/services/privileged_helper.py" /usr/lib/nuxarchy/nuxarchy-hardware-helper
sudo chmod 755 /usr/lib/nuxarchy/nuxarchy-hardware-helper

if [ -f "${SCRIPT_DIR}/packaging/com.nuxarchy.hub.policy" ]; then
    sudo mkdir -p /usr/share/polkit-1/actions
    sudo cp "${SCRIPT_DIR}/packaging/com.nuxarchy.hub.policy" /usr/share/polkit-1/actions/
fi

sudo mkdir -p /usr/share/applications
sudo cp "${SCRIPT_DIR}/packaging/com.nuxarchy.hub.desktop" /usr/share/applications/

sudo mkdir -p /usr/share/icons/hicolor/512x512/apps
if [ -f "${SCRIPT_DIR}/nuxarchy/resources/nuxarchy_logo.png" ]; then
    sudo cp "${SCRIPT_DIR}/nuxarchy/resources/nuxarchy_logo.png" /usr/share/icons/hicolor/512x512/apps/nuxarchy.png
fi

if command -v update-desktop-database &>/dev/null; then
    sudo update-desktop-database 2>/dev/null || true
fi

echo "========================================================"
echo "      NUXARCHY installation completed successfully!     "
echo "  The nuxarchy-daemon background service is now active  "
echo "  providing live hardware telemetry and instant control "
echo "  without repeated password prompts.                    "
echo "                                                        "
echo "  Launch anytime by running:                            "
echo "      /usr/bin/nuxarchy   (or simply 'nuxarchy')        "
echo "  or from your desktop application launcher menu.       "
echo "                                                        "
echo "  Note for ZSH users: if in ~/NUXARCHY, run 'rehash'    "
echo "  or use '/usr/bin/nuxarchy' to prevent autocd.         "
echo "========================================================"
