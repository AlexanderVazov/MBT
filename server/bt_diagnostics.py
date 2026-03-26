#!/usr/bin/env python3
"""
Bluetooth Diagnostics Script
Checks Bluetooth adapter status and configuration
"""

import subprocess
import sys
import os

def run_command(cmd, check_sudo=False):
    """Run a shell command and return output"""
    try:
        if check_sudo and os.geteuid() != 0:
            print(f"  ⚠️  Need sudo to run: {cmd}")
            return None, "Need sudo"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        return result.stdout + result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return None, "Timeout"
    except Exception as e:
        return None, str(e)

print("="*70)
print("  Bluetooth Adapter Diagnostics")
print("="*70)
print()

# Check 1: Bluetooth module availability
print("[1] Checking Python PyBluez module...")
try:
    import bluetooth
    print("  ✓ PyBluez is installed")
except ImportError:
    print("  ✗ PyBluez not installed")
    print("  FIX: sudo pip3 install pybluez")
    sys.exit(1)

# Check 2: Check if running with sudo
print("\n[2] Checking permissions...")
if os.geteuid() == 0:
    print("  ✓ Running with sudo/root privileges")
else:
    print("  ⚠️  NOT running with sudo")
    print("  FIX: Run with 'sudo python3 bt_diagnostics.py'")
    print("  NOTE: Bluetooth service advertising requires root privileges")

# Check 3: HCI devices
print("\n[3] Checking for Bluetooth adapters (hciconfig)...")
output, code = run_command("hciconfig")
if output:
    print(output)
    if "hci0" not in output:
        print("  ✗ No Bluetooth adapter found")
        print("  FIX: Check if Bluetooth hardware is enabled")
    else:
        if "UP RUNNING" in output:
            print("  ✓ Adapter is UP and RUNNING")
        else:
            print("  ✗ Adapter is DOWN")
            print("  FIX: Run 'sudo hciconfig hci0 up'")
        
        if "PSCAN" in output or "ISCAN" in output:
            print("  ✓ Adapter is scannable/discoverable")
        else:
            print("  ⚠️  Adapter might not be in discoverable mode")
            print("  FIX: Run 'sudo hciconfig hci0 piscan'")
else:
    print("  ⚠️  hciconfig not available or failed")

# Check 4: Bluetooth service
print("\n[4] Checking Bluetooth service status...")
output, code = run_command("systemctl status bluetooth")
if output:
    if "active (running)" in output:
        print("  ✓ Bluetooth service is running")
    elif "inactive" in output or "dead" in output:
        print("  ✗ Bluetooth service is NOT running")
        print("  FIX: sudo systemctl start bluetooth")
    else:
        print(f"  ? Status unclear:\n{output[:200]}")
else:
    print("  ⚠️  Could not check service status")

# Check 5: bluetoothctl show
print("\n[5] Checking adapter details (bluetoothctl)...")
output, code = run_command("bluetoothctl show")
if output:
    print(output)
    if "Powered: yes" in output:
        print("  ✓ Adapter is powered on")
    else:
        print("  ✗ Adapter is powered off")
        print("  FIX: Run 'sudo bluetoothctl' then type 'power on'")
    
    if "Discoverable: yes" in output:
        print("  ✓ Adapter is discoverable")
    else:
        print("  ⚠️  Adapter is not discoverable")
        print("  FIX: Run 'sudo bluetoothctl' then type 'discoverable on'")
else:
    print("  ⚠️  Could not get adapter details")

# Check 6: Try to get adapter address
print("\n[6] Testing Python Bluetooth API...")
try:
    devices = bluetooth.discover_devices(lookup_names=False, duration=1)
    print("  ✓ Bluetooth discover_devices() works")
except Exception as e:
    print(f"  ✗ Error testing Bluetooth API: {e}")

try:
    local_addr = bluetooth.read_local_bdaddr()
    print(f"  ✓ Local adapter address: {local_addr}")
except Exception as e:
    print(f"  ✗ Could not read local adapter address: {e}")

# Summary
print("\n" + "="*70)
print("  SUMMARY")
print("="*70)

if os.geteuid() != 0:
    print("\n⚠️  MOST LIKELY ISSUE: You need to run the server with sudo")
    print("   Try: sudo python3 bt_server.py")
else:
    print("\nIf all checks passed above, the server should work.")
    print("If some checks failed, follow the FIX instructions above.")

print("\nQuick fix commands to try:")
print("  1. sudo hciconfig hci0 up")
print("  2. sudo hciconfig hci0 piscan")
print("  3. sudo systemctl start bluetooth")
print("  4. sudo python3 bt_server.py")
print()
