#!/usr/bin/env python3
"""
Bluetooth SPP Server for Raspberry Pi
This server listens for incoming Bluetooth connections and handles data exchange
"""

import bluetooth
import sys
import signal
import time

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

def start_server():
    global server_sock, client_sock
    
    # Get local Bluetooth adapter address
    try:
        local_addr, local_name = bluetooth.read_local_bdaddr()
        print(f"[INFO] Local Bluetooth adapter: {local_addr}")
    except Exception as e:
        print(f"[ERROR] Could not read local Bluetooth adapter: {e}")
        print("[FIX] Make sure Bluetooth is enabled and you're running with sudo")
        sys.exit(1)
    
    # Create the Bluetooth socket using RFCOMM protocol
    server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    
    # Bind to the local adapter explicitly
    try:
        server_sock.bind((local_addr, bluetooth.PORT_ANY))
    except Exception as e:
        print(f"[WARNING] Could not bind to adapter {local_addr}: {e}")
        print("[INFO] Trying fallback binding method...")
        server_sock.bind(("", bluetooth.PORT_ANY))
    
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

def configure_wifi(sock, ssid, password):
    """Configure WiFi on Raspberry Pi"""
    import subprocess
    import os
    
    try:
        # Method 1: Using wpa_passphrase (recommended for WPA/WPA2)
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
            subprocess.run(['sudo', 'cp', '/etc/wpa_supplicant/wpa_supplicant.conf', 
                          '/etc/wpa_supplicant/wpa_supplicant.conf.backup'], 
                         timeout=5)
            
            # Append new network to wpa_supplicant.conf
            sock.send("Writing WiFi configuration...\n".encode('utf-8'))
            config_lines = [
                '\n# Added by Bluetooth WiFi Setup\n',
                wpa_config,
                '\n'
            ]
            
            with open('/tmp/wifi_network.conf', 'w') as f:
                f.write(''.join(config_lines))
            
            # Append to wpa_supplicant config
            subprocess.run(
                ['sudo', 'bash', '-c', 
                 'cat /tmp/wifi_network.conf >> /etc/wpa_supplicant/wpa_supplicant.conf'],
                timeout=5,
                check=True
            )
            
            # Remove temp file
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
                ['sudo', 'bash', '-c', 
                 'cat /tmp/wifi_network.conf >> /etc/wpa_supplicant/wpa_supplicant.conf'],
                timeout=5,
                check=True
            )
            os.remove('/tmp/wifi_network.conf')
        
        # Reconfigure wpa_supplicant
        sock.send("Restarting WiFi interface...\n".encode('utf-8'))
        subprocess.run(['sudo', 'wpa_cli', '-i', 'wlan0', 'reconfigure'], 
                      timeout=5, 
                      check=True)
        
        # Wait a moment for connection
        time.sleep(2)
        
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
