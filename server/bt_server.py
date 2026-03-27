#!/usr/bin/env python3
"""
Bluetooth SPP Server for Raspberry Pi
This server listens for incoming Bluetooth connections and handles data exchange
"""

import bluetooth
import sys
import signal
import time
import subprocess

server_sock = None
client_sock = None

def cleanup(signum=None, frame=None):
    """Clean up Bluetooth sockets on exit"""
    print("\n[INFO] Shutting down Bluetooth server...")
    if client_sock:
        try:
            client_sock.close()
        except:
            pass
    if server_sock:
        try:
            server_sock.close()
        except:
            pass
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

def setup_bluetooth():
    """Ensure Bluetooth is powered on and discoverable"""
    print("[INFO] Setting up Bluetooth adapter...")
    
    commands = [
        ("sudo hciconfig hci0 up", "Powering on Bluetooth adapter"),
        ("sudo hciconfig hci0 piscan", "Making Bluetooth discoverable"),
        ("sudo hciconfig hci0 sspmode 1", "Enabling Simple Pairing mode"),
    ]
    
    for cmd, description in commands:
        try:
            print(f"[INFO] {description}...")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"[SUCCESS] {description}")
            else:
                print(f"[WARNING] {description} failed: {result.stderr.strip()}")
        except subprocess.TimeoutExpired:
            print(f"[WARNING] {description} timed out")
        except Exception as e:
            print(f"[WARNING] {description} error: {e}")
    
    time.sleep(1)  # Give Bluetooth time to settle
    print("[SUCCESS] Bluetooth adapter setup complete\n")

def get_bluetooth_address():
    """Get Bluetooth adapter address using hciconfig"""
    try:
        result = subprocess.run(['hciconfig', 'hci0'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        
        # Parse output to find BD Address
        for line in result.stdout.split('\n'):
            if 'BD Address:' in line:
                addr = line.split('BD Address:')[1].strip().split()[0]
                return addr
        
        return None
    except Exception as e:
        print(f"[WARNING] Could not get BD address via hciconfig: {e}")
        return None

def start_server():
    global server_sock, client_sock
    
    # Setup Bluetooth adapter first
    setup_bluetooth()
    
    # Get local Bluetooth adapter address
    local_addr = None
    try:
        # First try PyBluez method
        local_addr, local_name = bluetooth.read_local_bdaddr()
        print(f"[INFO] Local Bluetooth adapter: {local_addr}")
    except Exception as e:
        print(f"[WARNING] PyBluez read_local_bdaddr failed: {e}")
        # Try alternative method using hciconfig
        local_addr = get_bluetooth_address()
        if local_addr:
            print(f"[INFO] Local Bluetooth adapter (via hciconfig): {local_addr}")
        else:
            print("[INFO] Could not determine adapter address, using fallback binding")
    
    # Create the Bluetooth socket using RFCOMM protocol
    server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    
    # Bind to the local adapter
    try:
        if local_addr:
            server_sock.bind((local_addr, bluetooth.PORT_ANY))
            print(f"[INFO] Bound to adapter {local_addr}")
        else:
            # Fallback: bind to any available adapter
            server_sock.bind(("", bluetooth.PORT_ANY))
            print("[INFO] Bound to default adapter")
    except Exception as e:
        print(f"[WARNING] Could not bind explicitly: {e}")
        print("[INFO] Trying fallback binding method...")
        server_sock.bind(("", bluetooth.PORT_ANY))
        print("[SUCCESS] Fallback binding succeeded")
    
    port = server_sock.getsockname()[1]
    
    # Start listening for incoming connections (backlog of 1)
    server_sock.listen(1)
    
    # UUID for SPP (Serial Port Profile)
    uuid = "00001101-0000-1000-8000-00805F9B34FB"
    
    # Advertise the service
    try:
        bluetooth.advertise_service(
            server_sock,
            "RPI Bridge Server",
            service_id=uuid,
            service_classes=[uuid, bluetooth.SERIAL_PORT_CLASS],
            profiles=[bluetooth.SERIAL_PORT_PROFILE]
        )
    except bluetooth.BluetoothError as e:
        print(f"[ERROR] Failed to advertise Bluetooth service: {e}")
        print()
        print("Common causes and fixes:")
        print("  1. Bluetooth not powered on:")
        print("     sudo bluetoothctl")
        print("     power on")
        print()
        print("  2. Bluetooth not discoverable:")
        print("     sudo bluetoothctl")
        print("     discoverable on")
        print()
        print("  3. Bluetooth service not running:")
        print("     sudo systemctl start bluetooth")
        print()
        server_sock.close()
        sys.exit(1)
    
    print(f"[INFO] Bluetooth SPP Server started")
    print(f"[INFO] Service Name: RPI Bridge Server")
    print(f"[INFO] UUID: {uuid}")
    print(f"[INFO] Listening on RFCOMM port {port}")
    print(f"[INFO] Waiting for connections...")
    
    try:
        while True:
            # Accept incoming connection
            client_sock, client_info = server_sock.accept()
            print(f"\n[SUCCESS] Accepted connection from {client_info}")
            
            try:
                # Handle the connected client
                handle_client(client_sock)
            except bluetooth.BluetoothError as e:
                print(f"[ERROR] Bluetooth error: {e}")
            except Exception as e:
                print(f"[ERROR] Client handler error: {e}")
            finally:
                if client_sock:
                    client_sock.close()
                    client_sock = None
                print("[INFO] Client disconnected. Waiting for new connections...")
    
    except KeyboardInterrupt:
        cleanup()
    except Exception as e:
        print(f"[ERROR] Server error: {e}")
        cleanup()

def handle_client(sock):
    """Handle data from connected client"""
    print("[INFO] Client connected. Ready to receive data.")
    
    try:
        while True:
            # Receive data (buffer size 1024 bytes)
            data = sock.recv(1024)
            
            if not data:
                print("[INFO] Client sent empty data (disconnecting)")
                break
            
            # Decode and display received data
            try:
                message = data.decode('utf-8').strip()
                print(f"[RECEIVED] {message}")
                
                # Check if this is WiFi configuration data
                if message.startswith('WIFI:'):
                    handle_wifi_config(sock, message)
                else:
                    # Echo back a response for other messages
                    response = f"Pi received: {message}\n"
                    sock.send(response.encode('utf-8'))
                    print(f"[SENT] {response.strip()}")
                
            except UnicodeDecodeError:
                # Handle binary data
                print(f"[RECEIVED] Binary data ({len(data)} bytes): {data.hex()}")
                sock.send(b"ACK\n")
    
    except bluetooth.BluetoothError as e:
        if "104" in str(e) or "Connection reset" in str(e):
            print("[INFO] Client disconnected")
        else:
            print(f"[ERROR] Bluetooth error during communication: {e}")
    except Exception as e:
        print(f"[ERROR] Error handling client: {e}")

def handle_wifi_config(sock, message):
    """Handle WiFi configuration request"""
    import subprocess
    import os
    
    try:
        # Parse message: WIFI:SSID:PASSWORD
        parts = message.split(':', 2)
        if len(parts) != 3:
            error_msg = "ERROR: Invalid WiFi format. Expected WIFI:SSID:PASSWORD\n"
            sock.send(error_msg.encode('utf-8'))
            print(f"[ERROR] {error_msg.strip()}")
            return
        
        ssid = parts[1]
        password = parts[2] if len(parts) > 2 else ""
        
        print(f"[WIFI] Configuring WiFi: SSID='{ssid}'")
        sock.send(f"Configuring WiFi network: {ssid}\n".encode('utf-8'))
        
        # Configure WiFi using wpa_passphrase and wpa_supplicant
        configure_wifi(sock, ssid, password)
        
    except Exception as e:
        error_msg = f"ERROR: WiFi configuration failed: {e}\n"
        sock.send(error_msg.encode('utf-8'))
        print(f"[ERROR] {error_msg.strip()}")

def uses_networkmanager():
    """Check if system uses NetworkManager for WiFi"""
    import subprocess
    try:
        result = subprocess.run(['systemctl', 'is-active', 'NetworkManager'],
                              capture_output=True, text=True, timeout=5)
        return result.stdout.strip() == 'active'
    except:
        return False

def configure_wifi_networkmanager(sock, ssid, password):
    """Configure WiFi using NetworkManager (nmcli)"""
    import subprocess
    
    sock.send("Using NetworkManager to configure WiFi...\n".encode('utf-8'))
    
    # Scan for networks first
    sock.send("Scanning for WiFi networks...\n".encode('utf-8'))
    subprocess.run(['sudo', 'nmcli', 'device', 'wifi', 'rescan'],
                  capture_output=True, timeout=10)
    time.sleep(3)  # Give time for scan to complete
    
    # Delete existing connection with same name if exists
    subprocess.run(['sudo', 'nmcli', 'connection', 'delete', ssid],
                  capture_output=True, timeout=10)
    
    # Try direct connect first (works if network is visible)
    sock.send(f"Connecting to WiFi network: {ssid}...\n".encode('utf-8'))
    
    if password:
        cmd = ['sudo', 'nmcli', 'device', 'wifi', 'connect', ssid, 
               'password', password]
    else:
        cmd = ['sudo', 'nmcli', 'device', 'wifi', 'connect', ssid]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    
    if result.returncode == 0:
        return result.stdout.strip()
    
    # If direct connect failed, create a saved connection profile
    # This will auto-connect when network becomes available
    sock.send("Network not visible. Creating saved profile...\n".encode('utf-8'))
    
    if password:
        cmd = ['sudo', 'nmcli', 'connection', 'add',
               'type', 'wifi',
               'con-name', ssid,
               'ssid', ssid,
               'wifi-sec.key-mgmt', 'wpa-psk',
               'wifi-sec.psk', password,
               'connection.autoconnect', 'yes']
    else:
        cmd = ['sudo', 'nmcli', 'connection', 'add',
               'type', 'wifi',
               'con-name', ssid,
               'ssid', ssid,
               'connection.autoconnect', 'yes']
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    
    if result.returncode != 0:
        raise Exception(f"nmcli failed: {result.stderr.strip()}")
    
    sock.send("WiFi profile saved. Will connect when network is in range.\n".encode('utf-8'))
    return result.stdout.strip()

def configure_wifi_wpa_supplicant(sock, ssid, password):
    """Configure WiFi using wpa_supplicant (legacy method)"""
    import subprocess
    import os
    
    wpa_conf = '/etc/wpa_supplicant/wpa_supplicant.conf'
    
    # Check if wpa_supplicant.conf exists, create if not
    if not os.path.exists(wpa_conf):
        sock.send("Creating wpa_supplicant.conf...\n".encode('utf-8'))
        base_config = '''ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=US
'''
        with open('/tmp/wpa_base.conf', 'w') as f:
            f.write(base_config)
        subprocess.run(['sudo', 'cp', '/tmp/wpa_base.conf', wpa_conf],
                      timeout=5, check=True)
        os.remove('/tmp/wpa_base.conf')
    
    if password:
        sock.send("Generating WPA configuration...\n".encode('utf-8'))
        
        # Generate WPA config
        result = subprocess.run(
            ['wpa_passphrase', ssid, password],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            raise Exception(f"wpa_passphrase failed: {result.stderr}")
        
        wpa_config = result.stdout
        
        # Backup existing config
        sock.send("Backing up current configuration...\n".encode('utf-8'))
        subprocess.run(['sudo', 'cp', wpa_conf, f'{wpa_conf}.backup'], timeout=5)
        
        # Append new network to wpa_supplicant.conf
        sock.send("Writing WiFi configuration...\n".encode('utf-8'))
        config_lines = [
            '\n# Added by Bluetooth WiFi Setup\n',
            wpa_config,
            '\n'
        ]
        
        with open('/tmp/wifi_network.conf', 'w') as f:
            f.write(''.join(config_lines))
        
        subprocess.run(
            ['sudo', 'bash', '-c', f'cat /tmp/wifi_network.conf >> {wpa_conf}'],
            timeout=5,
            check=True
        )
        
        os.remove('/tmp/wifi_network.conf')
        
    else:
        # Open network (no password)
        sock.send("Configuring open network...\n".encode('utf-8'))
        open_network = f'''
network={{
    ssid="{ssid}"
    key_mgmt=NONE
}}
'''
        with open('/tmp/wifi_network.conf', 'w') as f:
            f.write(open_network)
        
        subprocess.run(
            ['sudo', 'bash', '-c', f'cat /tmp/wifi_network.conf >> {wpa_conf}'],
            timeout=5,
            check=True
        )
        os.remove('/tmp/wifi_network.conf')
    
    # Reconfigure wpa_supplicant
    sock.send("Restarting WiFi interface...\n".encode('utf-8'))
    subprocess.run(['sudo', 'wpa_cli', '-i', 'wlan0', 'reconfigure'], 
                  timeout=5, check=True)

def configure_wifi(sock, ssid, password):
    """Configure WiFi on Raspberry Pi"""
    import subprocess
    
    try:
        # Check which WiFi management system is in use
        if uses_networkmanager():
            print("[WIFI] Using NetworkManager")
            configure_wifi_networkmanager(sock, ssid, password)
        else:
            print("[WIFI] Using wpa_supplicant")
            configure_wifi_wpa_supplicant(sock, ssid, password)
        
        # Wait a moment for connection
        time.sleep(3)
        
        # Check if connected
        result = subprocess.run(['iwgetid', '-r'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        
        connected_ssid = result.stdout.strip()
        
        if connected_ssid == ssid:
            success_msg = f"SUCCESS: Connected to {ssid}!\n"
            sock.send(success_msg.encode('utf-8'))
            print(f"[WIFI] {success_msg.strip()}")
        else:
            status_msg = f"WiFi configured. Current network: {connected_ssid if connected_ssid else 'Not connected yet'}\n"
            sock.send(status_msg.encode('utf-8'))
            sock.send("Note: It may take a few moments to connect. Check with 'iwgetid' command.\n".encode('utf-8'))
            print(f"[WIFI] {status_msg.strip()}")
        
    except subprocess.TimeoutExpired:
        error_msg = "ERROR: WiFi configuration timed out\n"
        sock.send(error_msg.encode('utf-8'))
        print(f"[ERROR] {error_msg.strip()}")
    except Exception as e:
        error_msg = f"ERROR: {str(e)}\n"
        sock.send(error_msg.encode('utf-8'))
        print(f"[ERROR] WiFi configuration error: {e}")

if __name__ == "__main__":
    print("="*60)
    print("  Raspberry Pi Bluetooth SPP Server")
    print("="*60)
    print()
    
    # Check if bluetooth module is available
    try:
        import bluetooth
    except ImportError:
        print("[ERROR] PyBluez not installed!")
        print("[FIX] Install it with: sudo pip3 install pybluez")
        sys.exit(1)
    
    start_server()
