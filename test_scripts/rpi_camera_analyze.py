#!/usr/bin/env python3
"""
Raspberry Pi Camera Script
Captures a photo from the RPi camera module and analyzes it with Google Gemini API
WITH TEXT-TO-SPEECH SUPPORT
"""

import google.genai as genai
import os
import sys
import base64
import mimetypes
from datetime import datetime
from tts_helper import speak_text

# Try importing picamera2 first (newer), fallback to picamera
try:
    from picamera2 import Picamera2
    USE_PICAMERA2 = True
except ImportError:
    try:
        from picamera import PiCamera
        USE_PICAMERA2 = False
    except ImportError:
        print("Error: Neither picamera2 nor picamera is installed.")
        print("Install with: sudo apt-get install -y python3-picamera2")
        print("Or: sudo pip3 install picamera")
        sys.exit(1)

# Configure the API key
api_key = os.getenv('GOOGLE_API_KEY')
if not api_key:
    raise ValueError("GOOGLE_API_KEY environment variable not set. Please set it and try again.")

client = genai.Client(api_key=api_key)

# Capture photo from camera
print("Initializing camera...")
try:
    if USE_PICAMERA2:
        picam2 = Picamera2()
        picam2.start()
        print("Capturing photo with picamera2...")
        image_path = f"/tmp/rpi_capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        picam2.capture_file(image_path)
        picam2.stop()
    else:
        camera = PiCamera()
        print("Capturing photo with picamera...")
        image_path = f"/tmp/rpi_capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        camera.capture(image_path)
        camera.close()
    
    print(f"Photo captured: {image_path}")
except Exception as e:
    print(f"Error capturing photo: {e}")
    sys.exit(1)

# Determine MIME type
mime_type, _ = mimetypes.guess_type(image_path)
if not mime_type:
    mime_type = 'image/jpeg'

print("-" * 50)

try:
    # Read and encode image as base64
    print("Reading image...")
    with open(image_path, 'rb') as img_file:
        image_data = base64.standard_b64encode(img_file.read()).decode('utf-8')
    
    print("Analyzing image with Gemini...")
    response = client.models.generate_content(
        model="models/gemini-flash-lite-latest",
        contents=[
            {
                "role": "user",
                "parts": [
                    {
                        "text": "What do you see in this image? Provide a brief one or two sentence description."
                    },
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": image_data
                        }
                    }
                ]
            }
        ]
    )
    
    print("Gemini Analysis:")
    print("-" * 50)
    print(response.text)
    print("-" * 50)
    print(f"Image saved at: {image_path}")
    
    # Speak the response
    print("\n[Speaking response...]")
    speak_text(response.text)
    
except Exception as e:
    print(f"Error: {e}")
finally:
    # Clean up: optionally delete the captured image
    # Uncomment the line below to automatically delete the image after analysis
    # import os
    # os.remove(image_path)
    pass
