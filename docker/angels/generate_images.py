#!/usr/bin/env python3
"""Generate horizontal thumbnail images using Gemini API."""

import base64
import json
import os
import sys
import urllib.request

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("Error: GEMINI_API_KEY not set")
    sys.exit(1)

MEDIA_DIR = "/home/judicandus/Downloads/Kolibri/media"
MODEL = "gemini-2.5-flash-image"


def call_gemini(parts, aspect_ratio="16:9"):
    """Call Gemini API with given parts and aspect ratio."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"
    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "imageConfig": {"aspectRatio": aspect_ratio},
        },
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        for part in result.get("candidates", [{}])[0].get("content", {}).get("parts", []):
            if "inlineData" in part:
                return base64.b64decode(part["inlineData"]["data"])
        print(f"  No image in response.")
        if "candidates" in result:
            for p in result["candidates"][0].get("content", {}).get("parts", []):
                if "text" in p:
                    print(f"  Text: {p['text'][:200]}")
    except Exception as e:
        print(f"  Failed: {e}")
    return None


def generate_horizontal_bible():
    """Generate horizontal version of bible.png with subject at 75% horizontal."""
    print("=== Generating horizontal Bible image ===")
    with open(os.path.join(MEDIA_DIR, "bible.png"), "rb") as f:
        bible_b64 = base64.b64encode(f.read()).decode("utf-8")

    prompt = (
        "Create a WIDE HORIZONTAL banner image based on this reference. "
        "Show an open illustrated Holy Bible with Old and New Testament artwork, "
        "warm candlelight, communion elements (grapes, chalice). "
        "Position the main Bible subject at the RIGHT side (75% from left). "
        "The left portion should be warm atmospheric background. "
        "Style: rich watercolor illustration, warm golden tones."
    )

    parts = [
        {"text": prompt},
        {"inline_data": {"mime_type": "image/png", "data": bible_b64}},
    ]

    img_data = call_gemini(parts, aspect_ratio="16:9")
    if img_data:
        out_path = os.path.join(MEDIA_DIR, "bible_horizontal.png")
        with open(out_path, "wb") as f:
            f.write(img_data)
        print(f"  Saved: {out_path}")
        return True
    print("  FAILED")
    return False


def generate_prologue():
    """Generate horizontal prologue image."""
    print("=== Generating Prologue image ===")

    prompt = (
        "Create a WIDE HORIZONTAL banner image for 'Prologue: The Bible as the Base'. "
        "Show an ancient scroll or parchment being unrolled revealing biblical text, "
        "with a sunrise over ancient hills and olive trees in the background. "
        "Position the main scroll subject at the RIGHT side (75% from left). "
        "The left portion shows dawn landscape with golden light. "
        "Style: rich watercolor illustration, warm golden and amber tones, "
        "biblical educational art style."
    )

    parts = [{"text": prompt}]

    img_data = call_gemini(parts, aspect_ratio="16:9")
    if img_data:
        out_path = os.path.join(MEDIA_DIR, "prologue.png")
        with open(out_path, "wb") as f:
            f.write(img_data)
        print(f"  Saved: {out_path}")
        return True
    print("  FAILED")
    return False


if __name__ == "__main__":
    ok1 = generate_horizontal_bible()
    ok2 = generate_prologue()
    if ok1 and ok2:
        print("\nAll images generated successfully!")
    else:
        print("\nSome images failed.")
        sys.exit(1)
