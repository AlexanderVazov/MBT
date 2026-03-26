#!/bin/bash
# PyBluez Installation Script for Raspberry Pi
# This script handles all the dependencies and builds PyBluez correctly

echo "=========================================="
echo " PyBluez Installation for Raspberry Pi"
echo "=========================================="
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "[ERROR] Please run with sudo:"
    echo "  sudo bash install_pybluez.sh"
    exit 1
fi

echo "[1/6] Updating package lists..."
apt-get update -qq

echo "[2/6] Installing Bluetooth development libraries..."
apt-get install -y bluetooth libbluetooth-dev bluez python3-dev python3-pip

echo "[3/6] Upgrading pip..."
pip3 install --upgrade pip

echo "[4/6] Installing PyBluez (this may take a few minutes)..."
pip3 install pybluez

echo "[5/6] Verifying installation..."
python3 -c "import bluetooth; print('PyBluez version:', bluetooth.__version__)" && echo "[OK] PyBluez installed successfully!" || echo "[ERROR] PyBluez installation failed!"

echo "[6/6] Enabling Bluetooth service..."
systemctl enable bluetooth
systemctl start bluetooth

echo
echo "=========================================="
echo " Installation Complete!"
echo "=========================================="
echo
echo "To test if PyBluez is working, run:"
echo "  python3 -c 'import bluetooth; print(bluetooth.__version__)'"
echo
echo "To start the Bluetooth server, run:"
echo "  sudo python3 bt_server.py"
echo
