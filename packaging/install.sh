#!/usr/bin/env bash
# ===================================================================
# NUXARCHY: Native Arch Linux Installer
# ===================================================================
set -euo pipefail

echo "========================================================"
echo "          Installing NUXARCHY for Arch Linux            "
echo "========================================================"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 1. Install dependencies via pacman
echo "[1/5] Checking and installing Arch Linux dependencies..."
if command -v pacman &>/dev/null; then
    sudo pacman -S --needed --noconfirm python python-pyside6 python-psutil polkit power-profiles-daemon
else
    echo "Warning: pacman not detected. Please ensure Python 3 and PySide6 are installed."
fi

# 2. Deploy to /opt/nuxarchy
echo "[2/5] Deploying application files to /opt/nuxarchy..."
sudo mkdir -p /opt/nuxarchy
sudo cp -r "${SCRIPT_DIR}/nuxarchy" /opt/nuxarchy/

# 3. Deploy launcher wrapper
echo "[3/5] Installing launcher to /usr/local/bin/nuxarchy..."
sudo tee /usr/local/bin/nuxarchy > /dev/null << 'EOF'
#!/bin/bash
export PYTHONPATH="/opt/nuxarchy:$PYTHONPATH"
exec python -m nuxarchy "$@"
EOF
sudo chmod +x /usr/local/bin/nuxarchy
sudo ln -sf /usr/local/bin/nuxarchy /usr/bin/nuxarchy

# 4. Install Polkit helper & policy
echo "[4/5] Configuring Polkit privileged hardware helper..."
sudo mkdir -p /usr/lib/nuxarchy
sudo cp "${SCRIPT_DIR}/nuxarchy/services/privileged_helper.py" /usr/lib/nuxarchy/nuxarchy-hardware-helper
sudo chmod 755 /usr/lib/nuxarchy/nuxarchy-hardware-helper

if [ -f "${SCRIPT_DIR}/packaging/com.nuxarchy.hub.policy" ]; then
    sudo mkdir -p /usr/share/polkit-1/actions
    sudo cp "${SCRIPT_DIR}/packaging/com.nuxarchy.hub.policy" /usr/share/polkit-1/actions/
fi

# 5. Deploy Desktop Launcher & Icon
echo "[5/5] Registering desktop application entry and icon..."
sudo mkdir -p /usr/share/applications
sudo cp "${SCRIPT_DIR}/packaging/com.nuxarchy.hub.desktop" /usr/share/applications/

sudo mkdir -p /usr/share/icons/hicolor/512x512/apps
if [ -f "${SCRIPT_DIR}/nuxarchy/resources/nuxarchy_logo.png" ]; then
    sudo cp "${SCRIPT_DIR}/nuxarchy/resources/nuxarchy_logo.png" /usr/share/icons/hicolor/512x512/apps/nuxarchy.png
fi

echo "========================================================"
echo "      NUXARCHY installation completed successfully!     "
echo "  Launch anytime by running 'nuxarchy' in your terminal "
echo "  or launching NUXARCHY from your application runner.   "
echo "========================================================"
