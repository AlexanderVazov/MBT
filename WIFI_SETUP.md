# WiFi Setup via Bluetooth

This system allows you to configure WiFi on your Raspberry Pi using a mobile app over Bluetooth.

## How It Works

1. **Mobile App** (Flutter) connects to Raspberry Pi via Bluetooth
2. **User enters WiFi credentials** (SSID and password) in the app
3. **App sends credentials** to the Pi using format: `WIFI:SSID:PASSWORD`
4. **Pi configures WiFi** automatically using `wpa_supplicant`
5. **Pi sends status updates** back to the mobile app

## Setup on Raspberry Pi

### 1. Start the Bluetooth Server
```bash
sudo python3 bt_server.py
```

The server will:
- Create a Bluetooth SPP (Serial Port Profile) service
- Wait for incoming connections
- Automatically handle WiFi configuration requests

### 2. Ensure Bluetooth is Properly Configured
```bash
# Power on Bluetooth
sudo bluetoothctl
> power on
> discoverable on
> exit
```

## Using the Mobile App

### 1. Scan for Devices
- Open the app
- Tap "Refresh Bonded Devices"
- Select your Raspberry Pi from the list

### 2. Connect
- Tap on your Pi device
- Wait for "Bluetooth Connected!" message

### 3. Configure WiFi
- Enter your WiFi network name (SSID)
- Enter your WiFi password
- Tap "Configure WiFi"

### 4. Monitor Progress
The app will show real-time updates:
- "Generating WPA configuration..."
- "Backing up current configuration..."
- "Writing WiFi configuration..."
- "Restarting WiFi interface..."
- "SUCCESS: Connected to [network]!"

## Server Features

### WiFi Configuration
The server automatically:
1. **Generates WPA configuration** using `wpa_passphrase`
2. **Backs up** existing `/etc/wpa_supplicant/wpa_supplicant.conf`
3. **Appends** new network configuration
4. **Reconfigures** wpa_supplicant without reboot
5. **Verifies** connection using `iwgetid`

### Security Features
- Backup of original WiFi config before changes
- Support for WPA/WPA2 encrypted networks
- Support for open (no password) networks
- Error handling and status reporting

## Protocol Format

### WiFi Configuration Request
```
WIFI:MyNetworkName:MyPassword123
```

### Server Responses
```
Configuring WiFi network: MyNetworkName
Generating WPA configuration...
Backing up current configuration...
Writing WiFi configuration...
Restarting WiFi interface...
SUCCESS: Connected to MyNetworkName!
```

### Error Messages
```
ERROR: Invalid WiFi format. Expected WIFI:SSID:PASSWORD
ERROR: WiFi configuration failed: [reason]
```

## Troubleshooting

### Server Won't Advertise
```bash
# Check Bluetooth status
sudo systemctl status bluetooth

# Restart Bluetooth service
sudo systemctl restart bluetooth

# Enable and power on
sudo bluetoothctl
> power on
> discoverable on
```

### WiFi Not Connecting
1. Check credentials are correct
2. Verify network is in range: `sudo iwlist wlan0 scan | grep SSID`
3. Check wpa_supplicant config: `sudo cat /etc/wpa_supplicant/wpa_supplicant.conf`
4. Manually reconfigure: `sudo wpa_cli -i wlan0 reconfigure`
5. Check status: `iwgetid -r`

### Restore WiFi Config
If something goes wrong:
```bash
sudo cp /etc/wpa_supplicant/wpa_supplicant.conf.backup \
       /etc/wpa_supplicant/wpa_supplicant.conf
sudo wpa_cli -i wlan0 reconfigure
```

## Manual WiFi Configuration

You can also test WiFi configuration manually via Bluetooth terminal:

```bash
# Connect via bluetooth terminal and send:
WIFI:YourNetworkName:YourPassword
```

## Required Permissions

The server needs sudo privileges to:
- Modify `/etc/wpa_supplicant/wpa_supplicant.conf`
- Execute `wpa_cli reconfigure`
- Run system WiFi commands

Always run with: `sudo python3 bt_server.py`

## Next Steps

After WiFi is configured, you can:
- SSH into the Pi over WiFi
- Access web services hosted on the Pi
- Continue using Bluetooth for other commands
- Disconnect Bluetooth (WiFi will remain configured)
