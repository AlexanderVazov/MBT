#!/usr/bin/env python3
"""
OCR Scanner module for MBT Raspberry Pi.

Pipeline:
  1. Capture image from Pi camera (picamera2) or USB webcam (OpenCV)
  2. Pre-process image for better OCR accuracy
  3. Extract text via pytesseract
  4. Match extracted text against the user's food preferences and allergies
  5. Return a structured result dict

Install dependencies on the Pi:
  sudo apt install tesseract-ocr python3-picamera2
  pip3 install pytesseract pillow opencv-python-headless
"""

import json
import os
import re
import subprocess
import tempfile
import time

# ── Dependency checks ─────────────────────────────────────────────────────────
try:
    import pytesseract
    from PIL import Image, ImageEnhance, ImageFilter
    TESSERACT_OK = True
except ImportError:
    TESSERACT_OK = False
    print("[OCR] pytesseract / Pillow not installed — OCR disabled")

# ── Preferences persistence ────────────────────────────────────────────────────
PREFS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "preferences.json")

_DEFAULT_PREFS = {"preferred": [], "allergies": []}


def load_preferences() -> dict:
    """Load food preferences from disk (written when phone sends PREFS:)."""
    if os.path.exists(PREFS_FILE):
        try:
            with open(PREFS_FILE, "r", encoding="utf-8") as fh:
                data = json.load(fh)
                if isinstance(data, dict):
                    return data
        except Exception as exc:
            print(f"[OCR] Could not read preferences file: {exc}")
    return dict(_DEFAULT_PREFS)


def save_preferences(prefs: dict) -> None:
    """Persist preferences to disk so they survive server restarts."""
    try:
        with open(PREFS_FILE, "w", encoding="utf-8") as fh:
            json.dump(prefs, fh, ensure_ascii=False, indent=2)
    except Exception as exc:
        print(f"[OCR] Could not save preferences: {exc}")


# ── Image capture ─────────────────────────────────────────────────────────────

def _capture_picamera2(path: str) -> bool:
    """Try picamera2 (official Pi camera library)."""
    try:
        from picamera2 import Picamera2  # type: ignore
        cam = Picamera2()
        cam.configure(cam.create_still_configuration())
        cam.start()
        time.sleep(2)           # warm-up / auto-exposure settle
        cam.capture_file(path)
        cam.stop()
        cam.close()
        print("[OCR] Captured via picamera2")
        return True
    except Exception as exc:
        print(f"[OCR] picamera2 failed: {exc}")
        return False


def _capture_libcamera(path: str) -> bool:
    """Try libcamera-still CLI (works when picamera2 is unavailable)."""
    try:
        result = subprocess.run(
            ["libcamera-still", "-o", path, "--timeout", "2000", "-n", "--nopreview"],
            capture_output=True,
            timeout=15,
        )
        if result.returncode == 0:
            print("[OCR] Captured via libcamera-still")
            return True
        print(f"[OCR] libcamera-still exit {result.returncode}: {result.stderr.decode()[:200]}")
    except Exception as exc:
        print(f"[OCR] libcamera-still failed: {exc}")
    return False


def _capture_opencv(path: str) -> bool:
    """Try OpenCV (USB webcam fallback)."""
    try:
        import cv2  # type: ignore
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return False
        time.sleep(1)
        ret, frame = cap.read()
        cap.release()
        if ret:
            cv2.imwrite(path, frame)
            print("[OCR] Captured via OpenCV (USB webcam)")
            return True
    except Exception as exc:
        print(f"[OCR] OpenCV failed: {exc}")
    return False


def capture_image() -> str | None:
    """
    Capture an image using the best available method.
    Returns path to a temporary JPEG, or None on failure.
    """
    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    tmp.close()
    path = tmp.name

    for attempt in (_capture_picamera2, _capture_libcamera, _capture_opencv):
        if attempt(path) and os.path.getsize(path) > 0:
            return path

    os.unlink(path)
    print("[OCR] No camera available")
    return None


# ── OCR ───────────────────────────────────────────────────────────────────────

def run_ocr(image_path: str) -> str:
    """
    Pre-process image and extract text with tesseract.
    Returns empty string on failure.
    """
    if not TESSERACT_OK:
        return ""
    try:
        img = Image.open(image_path)

        # Upscale small images — tesseract is happier with ≥300 dpi equivalent
        w, h = img.size
        if max(w, h) < 1000:
            scale = 1000 / max(w, h)
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

        # Greyscale → sharpen → high contrast
        img = img.convert("L")
        img = ImageEnhance.Contrast(img).enhance(2.5)
        img = img.filter(ImageFilter.SHARPEN)

        # PSM 6 = assume uniform block of text (good for food labels)
        text = pytesseract.image_to_string(img, config="--psm 6")
        return text.strip()
    except Exception as exc:
        print(f"[OCR] tesseract error: {exc}")
        return ""


# ── Food filtering ────────────────────────────────────────────────────────────

def _tokenise(text: str) -> list[str]:
    """Return all lowercase words and adjacent bigrams from text."""
    words = re.findall(r"[a-zA-Z\u00C0-\u024F]+", text.lower())
    bigrams = [f"{words[i]} {words[i + 1]}" for i in range(len(words) - 1)]
    return words + bigrams


def _matches(item: str, tokens: list[str]) -> bool:
    """True if any token contains the item string or vice-versa."""
    item_l = item.lower().strip()
    if not item_l:
        return False
    # Direct substring match (covers 'dairy' inside 'dairy-free', etc.)
    return any(item_l in tok or tok in item_l for tok in tokens)


def filter_food(text: str, prefs: dict) -> dict:
    """
    Match OCR text against the user's preferences and allergies.

    Returns:
        {
          "safe":            bool | None  (None if no text was detected),
          "allergens_found": list[str],
          "preferred_found": list[str],
          "summary":         str,
          "raw_text":        str          (first 500 chars of OCR output),
        }
    """
    if not text:
        return {
            "safe": None,
            "allergens_found": [],
            "preferred_found": [],
            "summary": "No text detected in the image.",
            "raw_text": "",
        }

    tokens = _tokenise(text)

    allergens_found = [
        item for item in prefs.get("allergies", []) if _matches(item, tokens)
    ]
    preferred_found = [
        item for item in prefs.get("preferred", []) if _matches(item, tokens)
    ]

    safe = len(allergens_found) == 0

    # Build human-readable summary
    parts = []
    if allergens_found:
        parts.append(f"ALLERGENS DETECTED: {', '.join(allergens_found)}")
    else:
        parts.append("No allergens detected")

    if preferred_found:
        parts.append(f"Contains your preferred items: {', '.join(preferred_found)}")

    summary = " | ".join(parts)

    return {
        "safe": safe,
        "allergens_found": allergens_found,
        "preferred_found": preferred_found,
        "summary": summary,
        "raw_text": text[:500],
    }


# ── Full pipeline ─────────────────────────────────────────────────────────────

def scan_and_filter(prefs: dict | None = None) -> dict:
    """
    Capture → OCR → filter.
    If prefs is None, loads from preferences.json on disk.
    Always returns a result dict (never raises).
    """
    if prefs is None:
        prefs = load_preferences()

    image_path = capture_image()
    if image_path is None:
        return {
            "safe": None,
            "allergens_found": [],
            "preferred_found": [],
            "summary": "Camera not available.",
            "raw_text": "",
        }

    try:
        text = run_ocr(image_path)
        return filter_food(text, prefs)
    except Exception as exc:
        print(f"[OCR] Unexpected error during scan: {exc}")
        return {
            "safe": None,
            "allergens_found": [],
            "preferred_found": [],
            "summary": f"Scan error: {exc}",
            "raw_text": "",
        }
    finally:
        try:
            os.unlink(image_path)
        except Exception:
            pass
