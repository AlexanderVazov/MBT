#!/usr/bin/env python3
"""
Simple Bluetooth adapter test
"""

import bluetooth
import sys

print("Testing Bluetooth adapter...")
print()

# Test 1: Get local adapter address
try:
    local_addr = bluetooth.read_local_bdaddr()
    print(f"✓ Local Bluetooth address: {local_addr[0]}")
except Exception as e:
    print(f"✗ Failed to read local adapter address: {e}")
    print("  This means no Bluetooth adapter is available to Python")
    sys.exit(1)

# Test 2: Create a socket
try:
    sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    print("✓ Created Bluetooth socket")
except Exception as e:
    print(f"✗ Failed to create socket: {e}")
    sys.exit(1)

# Test 3: Bind to adapter
try:
    # Try binding to the local adapter explicitly
    sock.bind((local_addr[0], bluetooth.PORT_ANY))
    port = sock.getsockname()[1]
    print(f"✓ Bound to adapter {local_addr[0]} on port {port}")
except Exception as e:
    print(f"✗ Failed to bind: {e}")
    try:
        # Fallback: try binding to empty string
        sock.bind(("", bluetooth.PORT_ANY))
        port = sock.getsockname()[1]
        print(f"✓ Bound to port {port} (fallback method)")
    except Exception as e2:
        print(f"✗ Fallback bind also failed: {e2}")
        sys.exit(1)

# Test 4: Listen
try:
    sock.listen(1)
    print("✓ Socket is listening")
except Exception as e:
    print(f"✗ Failed to listen: {e}")
    sys.exit(1)

# Test 5: Advertise service
try:
    uuid = "00001101-0000-1000-8000-00805F9B34FB"
    bluetooth.advertise_service(
        sock,
        "Test Server",
        service_id=uuid,
        service_classes=[uuid, bluetooth.SERIAL_PORT_CLASS],
        profiles=[bluetooth.SERIAL_PORT_PROFILE]
    )
    print("✓ Successfully advertising Bluetooth service!")
    print()
    print("SUCCESS! Your Bluetooth adapter works.")
    print("The bt_server.py should work now.")
except Exception as e:
    print(f"✗ Failed to advertise service: {e}")
    print()
    print("This is the same error as bt_server.py")
    print("Possible causes:")
    print("  1. Bluetooth adapter not in discoverable mode")
    print("  2. BlueZ service (bluetoothd) not running")
    print("  3. Adapter not powered on")
    print()
    print("Try these commands:")
    print("  sudo systemctl start bluetooth")
    print("  sudo bluetoothctl")
    print("  Then in bluetoothctl: power on")
    print("  Then in bluetoothctl: discoverable on")
    sys.exit(1)
finally:
    sock.close()

print()
print("Test complete!")
