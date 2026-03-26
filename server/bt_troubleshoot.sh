#!/bin/bash
# Bluetooth Troubleshooting Script for Raspberry Pi
# Run this on your Raspberry Pi to diagnose and fix Bluetooth issues

echo "=========================================="
echo " Bluetooth Troubleshooting Diagnostics"
echo "=========================================="
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "[ERROR] Please run with sudo:"
    echo "  sudo bash bt_troubleshoot.sh"
    exit 1
fi

echo "[1/8] Checking if Bluetooth is blocked by rfkill..."
rfkill list bluetooth
echo

echo "[2/8] Unblocking Bluetooth (if blocked)..."
rfkill unblock bluetooth
echo "[OK] Bluetooth unblocked"
echo

echo "[3/8] Checking Bluetooth service status..."
systemctl status bluetooth --no-pager | head -n 10
echo

echo "[4/8] Restarting Bluetooth service..."
systemctl restart bluetooth
sleep 2
echo "[OK] Bluetooth service restarted"
echo

echo "[5/8] Checking Bluetooth adapter status..."
hciconfig -a
echo

echo "[6/8] Powering up Bluetooth adapter..."
hciconfig hci0 up
sleep 1
echo "[OK] Adapter powered up"
echo

echo "[7/8] Making device discoverable and pairable..."
bluetoothctl <<EOF
power on
agent on
default-agent
discoverable on
pairable on
EOF
echo

echo "[8/8] Setting adapter to PISCAN mode..."
hciconfig hci0 piscan
echo

echo "=========================================="
echo " Diagnostics Complete!"
echo "=========================================="
echo
echo "Your Raspberry Pi should now be discoverable."
echo "Device information:"
hciconfig hci0 | grep -E "BD Address|UP RUNNING"
echo
echo "To verify discoverability, run:"
echo "  sudo hciconfig hci0"
echo
echo "Look for: 'UP RUNNING PSCAN ISCAN' in the output"
echo
