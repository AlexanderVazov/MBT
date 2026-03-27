#!/usr/bin/env python3
"""
HTTP Status Server for Raspberry Pi
Provides internet connectivity status to the RPI Bridge app via HTTP.
This allows the app to check if the Pi has internet WITHOUT Bluetooth pairing.

Run this alongside bt_server.py on the Raspberry Pi.
"""

import http.server
import socketserver
import subprocess
import json
import threading
import time

PORT = 8888

class StatusHandler(http.server.BaseHTTPRequestHandler):
    """Handle HTTP requests for status information"""
    
    def log_message(self, format, *args):
        """Override to add timestamp and prefix"""
        print(f"[HTTP] {self.address_string()} - {format % args}")
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/internet_status' or self.path == '/internet_status/':
            self.handle_internet_status()
        elif self.path == '/health' or self.path == '/health/':
            self.handle_health()
        else:
            self.send_error(404, 'Not Found')
    
    def handle_health(self):
        """Simple health check endpoint"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        response = json.dumps({'status': 'ok', 'service': 'rpi-bridge-status'})
        self.wfile.write(response.encode())
    
    def handle_internet_status(self):
        """Check if Pi has internet connectivity"""
        connected = check_internet_connection()
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = json.dumps({
            'status': 'connected' if connected else 'disconnected',
            'has_internet': connected
        })
        self.wfile.write(response.encode())


def check_internet_connection():
    """
    Check internet connectivity by pinging reliable servers.
    Returns True if internet is available, False otherwise.
    """
    # Try multiple hosts in case one is blocked
    hosts = [
        ('8.8.8.8', 'Google DNS'),
        ('1.1.1.1', 'Cloudflare DNS'),
        ('208.67.222.222', 'OpenDNS'),
    ]
    
    for host, name in hosts:
        try:
            # Use ping with short timeout (1 second, 1 packet)
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '1', host],
                capture_output=True,
                timeout=3
            )
            if result.returncode == 0:
                print(f"[STATUS] Internet check: Connected (via {name})")
                return True
        except subprocess.TimeoutExpired:
            continue
        except Exception as e:
            print(f"[WARNING] Ping to {name} failed: {e}")
            continue
    
    print("[STATUS] Internet check: Not connected")
    return False


class ThreadedHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Threaded HTTP server to handle multiple requests"""
    allow_reuse_address = True


def start_server():
    """Start the HTTP status server"""
    print("=" * 60)
    print("  Raspberry Pi Status Server")
    print("=" * 60)
    print()
    print(f"[INFO] Starting HTTP server on port {PORT}")
    print(f"[INFO] Endpoints:")
    print(f"       GET /internet_status - Check internet connectivity")
    print(f"       GET /health          - Health check")
    print()
    
    try:
        with ThreadedHTTPServer(("", PORT), StatusHandler) as httpd:
            print(f"[SUCCESS] Server running at http://0.0.0.0:{PORT}")
            print("[INFO] Press Ctrl+C to stop")
            print()
            httpd.serve_forever()
    except OSError as e:
        if 'Address already in use' in str(e):
            print(f"[ERROR] Port {PORT} is already in use!")
            print("[FIX] Stop the existing server or use a different port")
        else:
            print(f"[ERROR] Could not start server: {e}")
    except KeyboardInterrupt:
        print("\n[INFO] Server stopped")


if __name__ == "__main__":
    start_server()
