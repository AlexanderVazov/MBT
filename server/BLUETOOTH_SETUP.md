# Bluetooth Connection Setup Guide

## Problem
The Flutter app fails to connect with error: `read failed, socket might closed or timeout, read ret: -1`

## Root Cause
The Raspberry Pi doesn't have a Bluetooth SPP (Serial Port Profile) server running to accept incoming connections.

## Solution

### On Raspberry Pi:

#### 1. Install Required Packages
```bash
sudo apt-get update
sudo apt-get install -y bluetooth bluez python3-pip
sudo pip3 install pybluez
```

#### 2. Enable Bluetooth
```bash
sudo systemctl enable bluetooth
sudo systemctl start bluetooth
sudo bluetoothctl
# In bluetoothctl:
# - Type: power on
# - Type: agent on
# - Type: default-agent
# - Type: discoverable on
# - Type: pairable on
# - Type: exit
```

#### 3. Make Device Discoverable (Optional)
```bash
# Make Raspberry Pi visible to other devices
sudo hciconfig hci0 piscan
```

#### 4. Run the Bluetooth Server
```bash
cd /path/to/MBT
sudo python3 bt_server.py
```

**IMPORTANT**: The server MUST be running before you try to connect from the Android app!

#### 5. (Optional) Auto-start on Boot
Create a systemd service:

```bash
sudo nano /etc/systemd/system/bt-server.service
```

Add:
```ini
[Unit]
Description=Bluetooth SPP Server for RPI Bridge
After=bluetooth.service

[Service]
Type=simple
User=root
WorkingDirectory=/home/pi/MBT
ExecStart=/usr/bin/python3 /home/pi/MBT/bt_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable bt-server
sudo systemctl start bt-server
sudo systemctl status bt-server
```

### On Android App:

The Flutter app already has the connection logic. Just make sure:

1. Bluetooth is enabled on your phone
2. You've paired with the Raspberry Pi (Settings -> Bluetooth -> Pair)
3. The Raspberry Pi Bluetooth server is running
4. Then try connecting from the app

### Testing the Connection

1. On Raspberry Pi:
   ```bash
   sudo python3 bt_server.py
   ```
   You should see:
   ```
   [INFO] Bluetooth SPP Server started
   [INFO] Listening on RFCOMM port X
   [INFO] Waiting for connections...
   ```

2. On Android:
   - Open the app
   - Tap "Refresh Bonded Devices"
   - Tap on your Raspberry Pi device (maznopi)
   - You should see "Creating RFCOMM Link..."
   - After connection: "Bluetooth Connected!"

3. On Raspberry Pi (you should see):
   ```
   [SUCCESS] Accepted connection from ('XX:XX:XX:XX:XX:XX', X)
   [INFO] Client connected. Ready to receive data.
   ```

### Troubleshooting

#### If pairing fails:
```bash
# On Pi, remove old pairing:
sudo bluetoothctl
remove <PHONE_MAC_ADDRESS>
exit

# Then re-pair from your phone
```

#### If connection still fails:
```bash
# Check Bluetooth status:
sudo systemctl status bluetooth

# Check if server is running:
ps aux | grep bt_server

# Check Bluetooth logs:
sudo journalctl -u bluetooth -f
```

#### If you get "Permission denied":
Make sure to run the server with `sudo`:
```bash
sudo python3 bt_server.py
```

## Expected Behavior

When working correctly:
1. Raspberry Pi shows "Waiting for connections..."
2. Android app shows "Creating RFCOMM Link..."
3. Connection succeeds in ~2-5 seconds
4. App navigates to "Bluetooth Connected!" page
5. Raspberry Pi logs show "Accepted connection from..."

## Notes

- The SPP server uses UUID: `00001101-0000-1000-8000-00805F9B34FB` (standard SPP UUID)
- Connection timeout is 20 seconds
- The app will automatically try to refresh the bond if first attempt fails
- Make sure no other Bluetooth serial apps are using the same connection
