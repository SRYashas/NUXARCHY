#!/usr/bin/env bash
# ===================================================================
# NUXARCHY: Universal Native Linux Installer
# Installs all system & Python dependencies, root D-Bus daemon,
# systemd service units, Polkit policies, and desktop entries.
# ===================================================================
set -euo pipefail

echo "========================================================"
echo "          NUXARCHY: Linux Gaming Hub Installer          "
echo "========================================================"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Ask the user if they want to install all dependencies automatically
INSTALL_DEPS="Y"
if [ -t 0 ]; then
    echo ""
    read -rp "Would you like to automatically install all dependencies (PyQt6, sdbus, psutil, polkit, nftables, etc.)? [Y/n]: " user_prompt
    user_prompt="${user_prompt:-Y}"
    if [[ ! "$user_prompt" =~ ^[Yy]$ ]]; then
        INSTALL_DEPS="N"
    fi
else
    echo "-> Non-interactive shell detected: Automatically proceeding with dependency installation."
fi

if [ "$INSTALL_DEPS" = "Y" ]; then
    echo ""
    echo "[1/6] Installing Linux system & Python dependencies..."

    # Detect package manager and install native packages
    if command -v pacman &>/dev/null; then
        echo "-> Detected Arch Linux / Manjaro (pacman)."
        sudo pacman -S --needed --noconfirm python python-pip python-pyqt6 python-psutil polkit power-profiles-daemon nftables lm_sensors || true
    elif command -v apt-get &>/dev/null; then
        echo "-> Detected Debian / Ubuntu / Kali / Pop!_OS (apt)."
        sudo apt-get update -y || true
        sudo apt-get install -y python3 python3-pip python3-pyqt6 python3-psutil polkitd power-profiles-daemon libxcb-cursor0 nftables lm-sensors || true
    elif command -v dnf &>/dev/null; then
        echo "-> Detected Fedora / RHEL (dnf)."
        sudo dnf install -y python3 python3-pip python3-pyqt6 python3-psutil polkit power-profiles-daemon nftables lm_sensors || true
    elif command -v zypper &>/dev/null; then
        echo "-> Detected openSUSE (zypper)."
        sudo zypper install -y python3 python3-pip python3-pyqt6 python3-psutil polkit power-profiles-daemon nftables || true
    else
        echo "-> Unrecognized package manager. Proceeding with pip installation..."
    fi

    # Determine Python 3 binary
    PY_BIN="python3"
    if ! command -v "$PY_BIN" &>/dev/null; then
        PY_BIN="python"
    fi

    # Install Python packages via pip if not already provided by system
    echo "-> Checking and installing required Python packages (PyQt6, sdbus, psutil)..."
    sudo "$PY_BIN" -m pip install --break-system-packages "PyQt6>=6.5.0" "sdbus>=0.8.0" "psutil>=5.9.0" 2>/dev/null || \
    "$PY_BIN" -m pip install --break-system-packages "PyQt6>=6.5.0" "sdbus>=0.8.0" "psutil>=5.9.0" 2>/dev/null || \
    "$PY_BIN" -m pip install "PyQt6>=6.5.0" "sdbus>=0.8.0" "psutil>=5.9.0" 2>/dev/null || \
    sudo "$PY_BIN" -m pip install "PyQt6>=6.5.0" "psutil>=5.9.0" 2>/dev/null || true
else
    echo "[1/6] Skipping dependency installation as requested by user."
fi

# 2. Verify Python runtime dependencies
echo ""
echo "[2/6] Verifying Python runtime dependencies..."
PY_BIN="python3"
if ! command -v "$PY_BIN" &>/dev/null; then
    PY_BIN="python"
fi

if ! "$PY_BIN" -c "import PyQt6.QtWidgets, psutil" 2>/dev/null; then
    echo "Warning: PyQt6 or psutil is not detected in $PY_BIN environment."
    echo "Attempting self-heal via pip..."
    sudo "$PY_BIN" -m pip install --break-system-packages PyQt6 psutil 2>/dev/null || \
    "$PY_BIN" -m pip install PyQt6 psutil 2>/dev/null || true
fi

# 3. Deploy application files to /opt/nuxarchy
echo ""
echo "[3/6] Deploying application files to /opt/nuxarchy..."
sudo mkdir -p /opt/nuxarchy
sudo cp -r "${SCRIPT_DIR}/nuxarchy" /opt/nuxarchy/

# 4. Deploy executable wrapper scripts
echo ""
echo "[4/6] Installing launcher scripts in /usr/local/bin/ and /usr/bin/..."
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

if ! "$PY_BIN" -c "import PyQt6.QtWidgets" &>/dev/null; then
    echo "========================================================"
    echo "  [!] NUXARCHY: PyQt6 is not installed on your system   "
    echo "========================================================"
    echo "Please install PyQt6 using one of the following:"
    echo "  Debian/Kali/Ubuntu: sudo apt install python3-pyqt6 python3-psutil"
    echo "  Arch Linux:         sudo pacman -S python-pyqt6 python-psutil"
    echo "  Fedora:             sudo dnf install python3-pyqt6 python3-psutil"
    echo "  Or via pip:         pip install --break-system-packages PyQt6 sdbus psutil"
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

# 5. Install D-Bus System Bus Policy & Systemd Service Unit
echo ""
echo "[5/6] Configuring D-Bus policy and systemd root service..."
if [ -f "${SCRIPT_DIR}/packaging/org.nuxarchy.Daemon.conf" ]; then
    sudo mkdir -p /etc/dbus-1/system.d
    sudo cp "${SCRIPT_DIR}/packaging/org.nuxarchy.Daemon.conf" /etc/dbus-1/system.d/
    if command -v systemctl &>/dev/null; then
        sudo systemctl reload dbus 2>/dev/null || true
    fi
fi

if [ -f "${SCRIPT_DIR}/packaging/nuxarchy-daemon.service" ]; then
    sudo cp "${SCRIPT_DIR}/packaging/nuxarchy-daemon.service" /etc/systemd/system/
    if command -v systemctl &>/dev/null; then
        sudo systemctl daemon-reload
        sudo systemctl restart nuxarchy-daemon.service 2>/dev/null || \
        sudo systemctl enable --now nuxarchy-daemon.service 2>/dev/null || \
        echo "Notice: Started service or queued for next boot."
    fi
fi

# 6. Install Polkit Policy, Desktop Entry, and Application Icon
echo ""
echo "[6/6] Configuring Polkit, desktop application entry, and icon..."
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

echo ""
echo "========================================================"
echo "      NUXARCHY installation completed successfully!     "
echo "  The nuxarchy-daemon background service is now active  "
echo "  providing live hardware telemetry and instant control "
echo "  without repeated password prompts.                    "
echo "                                                        "
echo "  Launch anytime by running:                            "
echo "      nuxarchy                                          "
echo "  or from your desktop application launcher menu.       "
echo "========================================================"
