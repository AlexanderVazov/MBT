#!/usr/bin/env python3

import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*neon capable.*")

import os
import time
import base64
import asyncio
import socket
from datetime import datetime

import RPi.GPIO as GPIO
import google.genai as genai
from picamera2 import Picamera2
from libcamera import Transform, controls

# -----------------------------
# CAMERA SETUP
# -----------------------------
picam2 = Picamera2()
config = picam2.create_still_configuration(
    main={"size": (1920, 1080)},
    transform=Transform(vflip=True,hflip=True)
)
picam2.configure(config)
picam2.start()
time.sleep(2)

# Enable continuous autofocus for Pi Camera 3
try:
    picam2.set_controls({
        "AfMode": controls.AfModeEnum.Continuous
    })
   
    time.sleep(1.0)
    print("Autofocus enabled (continuous mode).")
except Exception as e:
    print(f"Autofocus not available or failed to enable: {e}")

# -----------------------------
# PINS
# -----------------------------
TRIG1, ECHO1 = 27, 22
TRIG2, ECHO2 = 17, 18
TRIG3, ECHO3 = 5, 6
TRIG4, ECHO4 = 21, 20

MOTOR1 = 4
MOTOR2 = 13
MOTOR3 = 26
MOTOR4 = 19

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

for m in [MOTOR1, MOTOR2, MOTOR3, MOTOR4]:
    GPIO.setup(m, GPIO.OUT)
    GPIO.output(m, GPIO.LOW)

GPIO.setup(BTN_LEFT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BTN_MIDDLE, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BTN_RIGHT, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# -----------------------------
# FUNCTIONS
# -----------------------------
async def speak_text(text):
    try:
        import edge_tts
        os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
        import pygame
        
        cyrillic_count = sum(1 for char in text if '\u0400' <= char <= '\u04FF')
        if len(text) > 0 and cyrillic_count / len(text) > 0.2:
            voice = "bg-BG-BorislavNeural"
        else:
            voice = "en-US-AriaNeural"
        
        audio_file = "/tmp/tts_audio.mp3"
        
        communicate = edge_tts.Communicate(text, voice=voice)
        await communicate.save(audio_file)
        
        pygame.mixer.init()
        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            await asyncio.sleep(0.1)
        
        pygame.mixer.music.unload()
        pygame.mixer.quit()
        
        if os.path.exists(audio_file):
            os.remove(audio_file)
            
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


def has_internet(host="generativelanguage.googleapis.com", port=443, timeout=2.0):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def capture_and_send(prompt):
    path = f"/tmp/img_{datetime.now().strftime('%H%M%S')}.jpg"
    picam2.capture_file(path)

    with open(path, "rb") as f:
        img = base64.b64encode(f.read()).decode()

    models = [
        "models/gemini-flash-lite-latest",
    ]

    if not has_internet():
        print("Network unavailable: cannot reach Gemini API")
        asyncio.run(speak_text("No internet connection. Please try again."))
        return

    for model in models:
        for attempt in range(2):
            try:
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
                asyncio.run(speak_text(response.text))
                return

            except Exception as e:
                print(f"Error with {model} (try {attempt + 1}/2): {e}")
                if attempt == 0:
                    time.sleep(1.0)

    asyncio.run(speak_text("AI service unavailable."))


# -------- VIBRATION --------
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
    
    if distance == -1:
        GPIO.output(motor_pin, GPIO.LOW)
        return

    if distance <= 0:
        GPIO.output(motor_pin, GPIO.LOW)
        return
    
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
print("System ready")

sensors_on = False
last_time = time.time()

DEBOUNCE_SEC = 0.35
last_left_press = 0.0
last_middle_press = 0.0
last_right_press = 0.0

prev_left = GPIO.input(BTN_LEFT)
prev_middle = GPIO.input(BTN_MIDDLE)
prev_right = GPIO.input(BTN_RIGHT)

try:
    while True:
        now = time.time()
        left_state = GPIO.input(BTN_LEFT)
        middle_state = GPIO.input(BTN_MIDDLE)
        right_state = GPIO.input(BTN_RIGHT)

        # -------- TEXT MODE --------
        if left_state == GPIO.LOW and prev_left == GPIO.HIGH and now - last_left_press >= DEBOUNCE_SEC:
            last_left_press = now
            capture_and_send(
                "Answer ONLY in Bulgarian. "
                "Read only clearly visible text. "
                "Focus on Bulgarian and English text. "
                "Ignore blurry, cut, or unreadable text. "
                "Do not describe objects unless necessary."
            )

        # -------- SCENE MODE --------
        if middle_state == GPIO.LOW and prev_middle == GPIO.HIGH and now - last_middle_press >= DEBOUNCE_SEC:
            last_middle_press = now
            capture_and_send(
                "Answer ONLY in Bulgarian. "
                "1-2 sentence description of the scene. "
                "Say only important and useful things. "
                "Ignore small or unclear details."
            )

        # -------- TOGGLE --------
        if right_state == GPIO.LOW and prev_right == GPIO.HIGH and now - last_right_press >= DEBOUNCE_SEC:
            last_right_press = now
            sensors_on = not sensors_on
            print("Sensors:", sensors_on)

        # -------- SENSORS --------
        if sensors_on and time.time() - last_time > 1:

            d1 = get_distance(TRIG1, ECHO1)
            time.sleep(0.2)
            d2 = get_distance(TRIG2, ECHO2)
            time.sleep(0.2)
            d3 = get_distance(TRIG3, ECHO3)
            time.sleep(0.2)
            d4 = get_distance(TRIG4, ECHO4)
            time.sleep(0.2)
            
            print(
                f"\rS1:{d1:.1f} S2:{d2:.1f} S3:{d3:.1f} S4:{d4:.1f} ", 
                end=""
            )

            handle_vibration(d1, MOTOR1)
            handle_vibration(d2, MOTOR2)
            handle_vibration(d3, MOTOR3)
            handle_vibration(d4, MOTOR4)

            last_time = time.time()

        prev_left = left_state
        prev_middle = middle_state
        prev_right = right_state

        if not sensors_on:
            GPIO.output(MOTOR1, GPIO.LOW)
            GPIO.output(MOTOR2, GPIO.LOW)
            GPIO.output(MOTOR3, GPIO.LOW)
            GPIO.output(MOTOR4, GPIO.LOW)

        time.sleep(0.02)

except KeyboardInterrupt:
    pass

finally:
    GPIO.cleanup()
    picam2.stop()