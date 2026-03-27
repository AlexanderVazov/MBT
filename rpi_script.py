#!/usr/bin/env python3

import os
import time
import base64
import asyncio
from datetime import datetime

import RPi.GPIO as GPIO
import google.genai as genai
from picamera2 import Picamera2

# -----------------------------
# CAMERA SETUP
# -----------------------------
picam2 = Picamera2()
config = picam2.create_still_configuration(main={"size": (1920, 1080)})
picam2.configure(config)
picam2.start()
time.sleep(2)

# -----------------------------
# PINS
# -----------------------------
TRIG1, ECHO1 = 27, 22
TRIG2, ECHO2 = 17, 18
TRIG3, ECHO3 = 5, 6   # ⚠️ may be unstable
TRIG4, ECHO4 = 21, 20

MOTOR1 = 4
MOTOR2 = 3
MOTOR3 = 2

BTN_LEFT = 12
BTN_MIDDLE = 0
BTN_RIGHT = 25

# -----------------------------
# CONSTANTS
# -----------------------------
SPEED = 34300
TIMEOUT = 0.04

# -----------------------------
# GEMINI
# -----------------------------
api_key = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

# -----------------------------
# GPIO SETUP
# -----------------------------
GPIO.setmode(GPIO.BCM)

for trig in [TRIG1, TRIG2, TRIG3, TRIG4]:
    GPIO.setup(trig, GPIO.OUT)
    GPIO.output(trig, False)

for echo in [ECHO1, ECHO2, ECHO3, ECHO4]:
    GPIO.setup(echo, GPIO.IN)

for m in [MOTOR1, MOTOR2, MOTOR3]:
    GPIO.setup(m, GPIO.OUT)
    GPIO.output(m, GPIO.LOW)

GPIO.setup(BTN_LEFT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BTN_MIDDLE, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BTN_RIGHT, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# -----------------------------
# FUNCTIONS
# -----------------------------
async def speak_text(text):
    """
    Convert text to audio using Edge TTS and play it.
    Auto-detects Bulgarian or English based on Cyrillic characters.
    """
    try:
        import edge_tts
        import pygame
        
        # Detect language
        cyrillic_count = sum(1 for char in text if '\u0400' <= char <= '\u04FF')
        if len(text) > 0 and cyrillic_count / len(text) > 0.2:
            voice = "bg-BG-BorislavNeural"  # Bulgarian
        else:
            voice = "en-US-AriaNeural"  # English
        
        # Create temporary audio file
        audio_file = "/tmp/tts_audio.mp3"
        
        # Generate speech
        communicate = edge_tts.Communicate(text, voice=voice)
        await communicate.save(audio_file)
        
        # Play audio
        pygame.mixer.init()
        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.play()
        
        # Wait for playback to finish
        while pygame.mixer.music.get_busy():
            await asyncio.sleep(0.1)
        
        # Cleanup
        pygame.mixer.music.unload()
        pygame.mixer.quit()
        
        # Delete temp file
        if os.path.exists(audio_file):
            os.remove(audio_file)
            
    except ImportError as e:
        print(f"TTS Error: Missing module - {e}")
        print("Install with: pip install edge-tts pygame")
    except Exception as e:
        print(f"TTS Error: {e}")


def get_distance(trig, echo):
    GPIO.output(trig, False)
    time.sleep(0.000002)

    GPIO.output(trig, True)
    time.sleep(0.00001)
    GPIO.output(trig, False)

    timeout = time.time() + TIMEOUT

    while GPIO.input(echo) == 0:
        if time.time() > timeout:
            return -1
    start = time.time()

    while GPIO.input(echo) == 1:
        if time.time() > timeout:
            return -1
    end = time.time()

    return (end - start) * SPEED / 2


def capture_and_send(prompt):
    path = f"/tmp/img_{datetime.now().strftime('%H%M%S')}.jpg"
    picam2.capture_file(path)

    with open(path, "rb") as f:
        img = base64.b64encode(f.read()).decode()

    # List of models to try (in order of preference)
    models = [
        "models/gemini-flash-lite-latest",
        "models/gemini-1.5-flash-latest",
        "models/gemini-1.5-flash"
    ]
    
    max_retries = 3
    base_delay = 2  # seconds
    
    for model in models:
        for attempt in range(max_retries):
            try:
                print(f"Trying {model} (attempt {attempt + 1}/{max_retries})...")
                response = client.models.generate_content(
                    model=model,
                    contents=[
                        {
                            "role": "user",
                            "parts": [
                                {"text": prompt},
                                {"inline_data": {"mime_type": "image/jpeg", "data": img}}
                            ]
                        }
                    ]
                )

                print("\nAI:", response.text)
                
                # Speak the response using TTS
                asyncio.run(speak_text(response.text))
                return  # Success, exit function
                
            except Exception as e:
                error_msg = str(e)
                
                # Check if it's a 503 error
                if "503" in error_msg or "UNAVAILABLE" in error_msg:
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)  # Exponential backoff
                        print(f"Model unavailable. Retrying in {delay}s...")
                        time.sleep(delay)
                    else:
                        print(f"{model} unavailable after {max_retries} attempts. Trying next model...")
                        break  # Try next model
                else:
                    # For other errors, print and try next model
                    print(f"Error with {model}: {error_msg}")
                    break
    
    # If all models fail
    print("ERROR: All models failed. Please try again later.")
    asyncio.run(speak_text("Sorry, the AI service is currently unavailable. Please try again later."))


# -------- VIBRATION FUNCTIONS --------
def vibrate_once(pin):
    GPIO.output(pin, GPIO.HIGH)
    time.sleep(0.15)
    GPIO.output(pin, GPIO.LOW)

def vibrate_twice(pin):
    for _ in range(2):
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(0.12)
        GPIO.output(pin, GPIO.LOW)
        time.sleep(0.12)

def vibrate_continuous(pin, duration=1.0):
    GPIO.output(pin, GPIO.HIGH)
    time.sleep(duration)
    GPIO.output(pin, GPIO.LOW)

def handle_vibration(distance, motor_pin):
    if distance > 0 and distance < 20:
        vibrate_continuous(motor_pin)

    elif distance < 50:
        vibrate_twice(motor_pin)

    elif distance < 100:
        vibrate_once(motor_pin)

    else:
        GPIO.output(motor_pin, GPIO.LOW)

# -----------------------------
# MAIN
# -----------------------------
print("System ready (FULL MODE + PATTERNS)")

sensors_on = False
last_time = time.time()

try:
    while True:

        # -------- BUTTON LEFT (TEXT) --------
        if GPIO.input(BTN_LEFT) == GPIO.LOW:
            print("\nReading text...")
            capture_and_send("Read all text in this image.")
            time.sleep(0.3)
            while GPIO.input(BTN_LEFT) == GPIO.LOW:
                time.sleep(0.05)

        # -------- BUTTON MIDDLE (DESCRIPTION) --------
        if GPIO.input(BTN_MIDDLE) == GPIO.LOW:
            print("\nDescribing scene...")
            capture_and_send("Describe the scene (left, center, right).")
            time.sleep(0.3)
            while GPIO.input(BTN_MIDDLE) == GPIO.LOW:
                time.sleep(0.05)

        # -------- BUTTON RIGHT (TOGGLE SENSORS) --------
        if GPIO.input(BTN_RIGHT) == GPIO.LOW:
            sensors_on = not sensors_on
            print("Sensors:", "ON" if sensors_on else "OFF")
            time.sleep(0.3)
            while GPIO.input(BTN_RIGHT) == GPIO.LOW:
                time.sleep(0.05)

        # -------- SENSOR LOGIC --------
        if sensors_on and time.time() - last_time > 1:

            d1 = get_distance(TRIG1, ECHO1)
            time.sleep(0.25)

            d2 = get_distance(TRIG2, ECHO2)
            time.sleep(0.25)

            d3 = get_distance(TRIG3, ECHO3)
            time.sleep(0.25)

            d4 = get_distance(TRIG4, ECHO4)

            print(f"S1: {d1:.1f} | S2: {d2:.1f} | S3: {d3:.1f} | S4: {d4:.1f}")

            # -------- VIBRATION CONTROL --------
            handle_vibration(d1, MOTOR1)
            handle_vibration(d2, MOTOR2)
            handle_vibration(d3, MOTOR3)

            last_time = time.time()

        # Safety
        if not sensors_on:
            GPIO.output(MOTOR1, GPIO.LOW)
            GPIO.output(MOTOR2, GPIO.LOW)
            GPIO.output(MOTOR3, GPIO.LOW)

        time.sleep(0.02)

except KeyboardInterrupt:
    print("Exiting...")

finally:
    GPIO.cleanup()
picam2.stop()