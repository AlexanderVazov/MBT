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
    
    # Create the Bluetooth socket using RFCOMM protocol
    server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    
    # Bind to any available port
    server_sock.bind(("", bluetooth.PORT_ANY))
    port = server_sock.getsockname()[1]
    
    # Start listening for incoming connections (backlog of 1)
    server_sock.listen(1)
    
    # UUID for SPP (Serial Port Profile)
    uuid = "00001101-0000-1000-8000-00805F9B34FB"
    
    # Advertise the service
    bluetooth.advertise_service(
        server_sock,
        "RPI Bridge Server",
        service_id=uuid,
        service_classes=[uuid, bluetooth.SERIAL_PORT_CLASS],
        profiles=[bluetooth.SERIAL_PORT_PROFILE]
    )
    
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
                message = data.decode('utf-8')
                print(f"[RECEIVED] {message}")
                
                # Echo back a response
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
