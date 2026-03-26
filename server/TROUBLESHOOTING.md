# Bluetooth Troubleshooting Guide

## PyBluez Installation Issues

### Symptom
Running `bt_server.py` fails with:
```
ModuleNotFoundError: No module named 'bluetooth'
```

### Solution - Install PyBluez correctly

**Option 1: Use the installation script**
```bash
cd /path/to/MBT
sudo bash install_pybluez.sh
```

**Option 2: Manual installation**

Run these commands on your Raspberry Pi:

```bash
# 1. Install Bluetooth development libraries
sudo apt-get update
sudo apt-get install -y bluetooth libbluetooth-dev bluez python3-dev python3-pip

# 2. Upgrade pip
sudo pip3 install --upgrade pip

# 3. Install PyBluez
sudo pip3 install pybluez

# 4. Verify installation
python3 -c "import bluetooth; print('PyBluez installed:', bluetooth.__version__)"
```

If you see a version number (e.g., "0.23"), PyBluez is installed correctly!

### Common Installation Errors

**Error: "Failed building wheel for pybluez"**

Solution:
```bash
sudo apt-get install -y libbluetooth-dev python3-dev build-essential
sudo pip3 install pybluez
```

**Error: "bluetooth/bluetooth.h: No such file or directory"**

Solution:
```bash
sudo apt-get install -y libbluetooth-dev
sudo pip3 install pybluez
```

**Error: "externally-managed-environment"** (Debian Bookworm / Python 3.11+)

Solution - Use one of these methods:

Method 1 (Recommended - use pipx):
```bash
sudo apt-get install -y pipx
pipx install pybluez
# Then run server with: pipx run python3 bt_server.py
```

Method 2 (Use system package if available):
```bash
sudo apt-get install -y python3-bluez
```

Method 3 (Override the restriction - use with caution):
```bash
sudo pip3 install pybluez --break-system-packages
```

Method 4 (Use virtual environment):
```bash
python3 -m venv ~/bt_venv
source ~/bt_venv/bin/activate
pip install pybluez
# Then run: sudo ~/bt_venv/bin/python3 bt_server.py
```

### Verify Installation

After installation, test it:

```bash
# Test 1: Import the module
python3 -c "import bluetooth; print('Success!')"

# Test 2: Check Bluetooth adapter
python3 -c "import bluetooth; print('Nearby devices:', bluetooth.discover_devices())"

# Test 3: Run the server
sudo python3 bt_server.py
```

---

# Bluetooth Not Discoverable - Troubleshooting Guide

## Symptom
Raspberry Pi doesn't appear in Bluetooth device lists (neither in Android Settings nor in the app), even after pressing the "make discoverable" button.

## Quick Fix (Run on Raspberry Pi)

### Option 1: Use the troubleshooting script
```bash
cd /path/to/MBT
sudo bash bt_troubleshoot.sh
```

### Option 2: Manual commands
Run these commands on your Raspberry Pi:

```bash
# 1. Check if Bluetooth is blocked
sudo rfkill list bluetooth

# 2. Unblock Bluetooth if blocked
sudo rfkill unblock bluetooth

# 3. Restart Bluetooth service
sudo systemctl restart bluetooth

# 4. Power up the adapter
sudo hciconfig hci0 up

# 5. Configure Bluetooth for discoverability
sudo bluetoothctl
# Then in bluetoothctl, type each command:
power on
agent on
default-agent
discoverable on
pairable on
exit

# 6. Enable PISCAN mode (discoverable + connectable)
sudo hciconfig hci0 piscan

# 7. Verify it's working
sudo hciconfig hci0
```

## What to Look For

After running the commands, `sudo hciconfig hci0` should show:
```
hci0:   Type: Primary  Bus: UART
        BD Address: XX:XX:XX:XX:XX:XX
        UP RUNNING PSCAN ISCAN    <--- This is what you want to see!
        RX bytes:... TX bytes:...
```

**Key flags:**
- `UP` - Adapter is powered on
- `RUNNING` - Adapter is active
- `PSCAN` - Page scan (connectable)
- `ISCAN` - Inquiry scan (discoverable)

If you don't see `PSCAN ISCAN`, the device won't be discoverable.

## Common Issues & Solutions

### Issue 1: Bluetooth service not running
**Symptom:** `systemctl status bluetooth` shows "inactive (dead)"

**Fix:**
```bash
sudo systemctl enable bluetooth
sudo systemctl start bluetooth
sudo systemctl status bluetooth
```

### Issue 2: Adapter blocked by rfkill
**Symptom:** `rfkill list` shows "Soft blocked: yes" or "Hard blocked: yes"

**Fix:**
```bash
sudo rfkill unblock bluetooth
# If hard blocked, check for physical switch on the device
```

### Issue 3: Adapter is down
**Symptom:** `hciconfig hci0` shows "DOWN" instead of "UP RUNNING"

**Fix:**
```bash
sudo hciconfig hci0 up
sudo hciconfig hci0 piscan
```

### Issue 4: Bluetooth times out or auto-disables
**Symptom:** Device is discoverable for a few seconds, then disappears

**Fix:**
```bash
# Make it permanently discoverable (no timeout)
sudo bluetoothctl
discoverable on
discoverable-timeout 0
exit
```

### Issue 5: Can't see adapter at all
**Symptom:** `hciconfig` returns nothing or "No such device"

**Fix:**
```bash
# Check if Bluetooth hardware is detected
lsusb | grep -i bluetooth  # For USB Bluetooth
dmesg | grep -i bluetooth   # Check kernel logs

# Reboot the Pi
sudo reboot
```

### Issue 6: Previously paired devices interfere
**Symptom:** Can't discover or pair with new devices

**Fix:**
```bash
# Remove all paired devices
sudo bluetoothctl
devices  # List all devices
remove XX:XX:XX:XX:XX:XX  # Remove each one
exit
```

## Complete Reset (Nuclear Option)

If nothing works, completely reset Bluetooth:

```bash
# 1. Stop Bluetooth
sudo systemctl stop bluetooth

# 2. Remove pairing database
sudo rm -rf /var/lib/bluetooth/*

# 3. Restart Bluetooth
sudo systemctl start bluetooth

# 4. Reconfigure
sudo bluetoothctl <<EOF
power on
agent on
default-agent
discoverable on
pairable on
discoverable-timeout 0
EOF

# 5. Enable PISCAN
sudo hciconfig hci0 piscan

# 6. Verify
sudo hciconfig hci0
```

## Verification Steps

1. **On Raspberry Pi:**
   ```bash
   sudo hciconfig hci0
   # Should show: UP RUNNING PSCAN ISCAN
   ```

2. **On Android:**
   - Go to Settings → Bluetooth
   - Tap "Scan for devices" or "Pair new device"
   - Your Pi should appear within 5-10 seconds
   - Device name should be visible (e.g., "maznopi" or "raspberrypi")

3. **In the App:**
   - If already paired: Tap "Refresh Bonded Devices"
   - If not paired: Pair via Android Settings first, then refresh in app

## Making Changes Permanent

To ensure Bluetooth stays discoverable after reboot:

```bash
# Create auto-config script
sudo nano /etc/systemd/system/bluetooth-config.service
```

Add this content:
```ini
[Unit]
Description=Bluetooth Auto Configuration
After=bluetooth.service

[Service]
Type=oneshot
ExecStartPre=/bin/sleep 5
ExecStart=/usr/bin/bluetoothctl -- power on
ExecStart=/usr/bin/bluetoothctl -- discoverable on
ExecStart=/usr/bin/bluetoothctl -- pairable on
ExecStart=/usr/sbin/hciconfig hci0 piscan
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

Enable it:
```bash
sudo systemctl daemon-reload
sudo systemctl enable bluetooth-config
sudo systemctl start bluetooth-config
```

## Debug Logging

If you're still having issues, collect debug info:

```bash
# Check system logs
sudo journalctl -u bluetooth -n 50 --no-pager

# Check Bluetooth daemon status
ps aux | grep bluetoothd

# Check kernel messages
dmesg | grep -i bluetooth | tail -n 20

# Test with bluetoothctl in interactive mode
sudo bluetoothctl
# Type: scan on
# See if other devices are detected
```

## Still Not Working?

If the Pi still doesn't appear:

1. **Check Bluetooth hardware:**
   ```bash
   sudo hciconfig -a
   # If no output, hardware may be faulty
   ```

2. **Try external USB Bluetooth adapter:**
   - Plug in USB Bluetooth dongle
   - Reboot Pi
   - Run setup commands again

3. **Update firmware/packages:**
   ```bash
   sudo apt update
   sudo apt upgrade
   sudo apt install --reinstall bluez bluetooth
   sudo reboot
   ```

## Next Steps After Fix

Once your Pi is discoverable again:

1. Pair from Android Settings
2. Approve pairing on both devices
3. Open the app
4. Tap "Refresh Bonded Devices"
5. Make sure `bt_server.py` is running: `sudo python3 bt_server.py`
6. Tap your Pi device to connect
7. Connection should succeed with the race condition fix!
