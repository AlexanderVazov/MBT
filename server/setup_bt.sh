#!/bin/bash
# Quick setup script for Raspberry Pi Bluetooth Server

echo "=========================================="
echo " RPI Bluetooth Server Setup"
echo "=========================================="
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "[ERROR] Please run with sudo:"
    echo "  sudo ./setup_bt.sh"
    exit 1
fi

# Install dependencies
echo "[1/4] Installing Bluetooth packages..."
apt-get update -qq
apt-get install -y bluetooth bluez python3-pip

echo "[2/4] Installing PyBluez..."
pip3 install pybluez

# Enable Bluetooth service
echo "[3/4] Enabling Bluetooth service..."
systemctl enable bluetooth
systemctl start bluetooth

# Configure Bluetooth
echo "[4/4] Configuring Bluetooth..."
bluetoothctl <<EOF
power on
agent on
default-agent
discoverable on
pairable on
EOF

# Make discoverable
hciconfig hci0 piscan

echo
echo "=========================================="
echo " Setup Complete!"
echo "=========================================="
echo
echo "To start the Bluetooth server, run:"
echo "  sudo python3 bt_server.py"
echo
echo "To make it auto-start on boot, run:"
echo "  sudo systemctl enable bt-server"
echo
echo "Device MAC Address:"
hciconfig hci0 | grep "BD Address"
echo
