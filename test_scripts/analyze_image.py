#!/usr/bin/env python3
"""
Script to analyze an image using Google Gemini API
Uploads the image and asks Gemini what it sees
WITH TEXT-TO-SPEECH SUPPORT
"""

import google.genai as genai
import os
import sys
import base64
import mimetypes
from pathlib import Path
from tts_helper import speak_text

# Configure the API key
api_key = os.getenv('GOOGLE_API_KEY')
if not api_key:
    raise ValueError("GOOGLE_API_KEY environment variable not set. Please set it and try again.")

client = genai.Client(api_key=api_key)

# Get image filename from command line or use default
if len(sys.argv) > 1:
    image_path = sys.argv[1]
else:
    # Default to first image file found in current directory
    image_files = list(Path('.').glob('*.png')) + list(Path('.').glob('*.jpg')) + list(Path('.').glob('*.jpeg')) + list(Path('.').glob('*.gif'))
    if not image_files:
        print("Error: No image file specified and no images found in current directory.")
        print("Usage: python analyze_image.py <image_path>")
        sys.exit(1)
    image_path = str(image_files[0])

# Check if file exists
if not os.path.exists(image_path):
    print(f"Error: Image file not found: {image_path}")
    sys.exit(1)

print(f"Analyzing image: {image_path}")
print("-" * 50)

# Determine MIME type
mime_type, _ = mimetypes.guess_type(image_path)
if not mime_type:
    mime_type = 'image/jpeg'

try:
    # Read and encode image as base64
    print("Reading image...")
    with open(image_path, 'rb') as img_file:
        image_data = base64.standard_b64encode(img_file.read()).decode('utf-8')
    
    print("Analyzing image...")
    response = client.models.generate_content(
        model="models/gemini-flash-lite-latest",
        contents=[
            {
                "role": "user",
                "parts": [
                    {
                        "text": "What do you see in this image? Please provide a detailed description."
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
    
    # Speak the response
    print("\n[Speaking response...]")
    speak_text(response.text)
    
except Exception as e:
    print(f"Error: {e}")

