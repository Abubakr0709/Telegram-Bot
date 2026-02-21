#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Render hadith quote cards with Islamic background imagery.
"""

from __future__ import annotations

import hashlib
import io
import os
import random
from functools import lru_cache

import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

CARD_WIDTH = 1080
CARD_HEIGHT = 1350
MARGIN = 88
TEXT_COLOR = (255, 255, 255)
REF_COLOR = (240, 245, 250)

# Curated Islamic imagery keywords for Unsplash
ISLAMIC_KEYWORDS = [
    "mosque",
    "quran",
    "islamic+calligraphy",
    "mecca",
    "kaaba",
    "islamic+architecture",
    "prayer+mat",
    "ramadan",
    "muslim+prayer",
    "islamic+art",
    "masjid",
    "dome+mosque",
    "minaret",
    "arabic+calligraphy",
]

UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "")
_IMAGE_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".image_cache")
os.makedirs(_IMAGE_CACHE_DIR, exist_ok=True)


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "DejaVuSans.ttf",
        "arial.ttf",
    ]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size=size)
        except Exception:
            continue
    return ImageFont.load_default()


def _get_islamic_image() -> Image.Image:
    """
    Fetch or load a high-resolution Islamic background image.
    Falls back to gradient if fetching fails.
    """
    # Try Unsplash if API key is available
    if UNSPLASH_ACCESS_KEY:
        try:
            keyword = random.choice(ISLAMIC_KEYWORDS)
            url = f"https://api.unsplash.com/photos/random?query={keyword}&orientation=portrait&client_id={UNSPLASH_ACCESS_KEY}"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                img_url = data["urls"]["regular"]  # 1080px width
                img_response = requests.get(img_url, timeout=15)
                if img_response.status_code == 200:
                    img = Image.open(io.BytesIO(img_response.content))
                    # Resize and crop to fit card dimensions
                    return _prepare_background(img)
        except Exception:
            pass
    
    # Fallback: Try cached images
    cache_files = [f for f in os.listdir(_IMAGE_CACHE_DIR) if f.endswith(('.jpg', '.jpeg', '.png'))]
    if cache_files:
        try:
            img_path = os.path.join(_IMAGE_CACHE_DIR, random.choice(cache_files))
            img = Image.open(img_path)
            return _prepare_background(img)
        except Exception:
            pass
    
    # Final fallback: Use a beautiful Islamic-themed gradient
    return _islamic_gradient(CARD_WIDTH, CARD_HEIGHT)


def _prepare_background(img: Image.Image) -> Image.Image:
    """Resize, crop, and enhance an image to fit the card perfectly."""
    # Convert to RGB if needed
    if img.mode != "RGB":
        img = img.convert("RGB")
    
    # Calculate aspect ratios
    img_ratio = img.width / img.height
    card_ratio = CARD_WIDTH / CARD_HEIGHT
    
    # Resize to cover the card area
    if img_ratio > card_ratio:
        new_height = CARD_HEIGHT
        new_width = int(new_height * img_ratio)
    else:
        new_width = CARD_WIDTH
        new_height = int(new_width / img_ratio)
    
    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Center crop to card dimensions
    left = (new_width - CARD_WIDTH) // 2
    top = (new_height - CARD_HEIGHT) // 2
    img = img.crop((left, top, left + CARD_WIDTH, top + CARD_HEIGHT))
    
    # Enhance: slight blur + darken for text readability
    img = img.filter(ImageFilter.GaussianBlur(radius=1.5))
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(0.5)  # Darken to 50%
    
    return img


def _islamic_gradient(width: int, height: int) -> Image.Image:
    """
    Create an Islamic-themed gradient background.
    Deep teal to dark blue with subtle texture.
    """
    img = Image.new("RGB", (width, height), (14, 40, 52))
    draw = ImageDraw.Draw(img)
    
    # Gradient from deep teal to dark navy
    top_rgb = (14, 40, 52)      # Deep teal
    bottom_rgb = (8, 20, 35)     # Dark navy
    
    for y in range(height):
        ratio = y / float(height - 1)
        r = int(top_rgb[0] * (1.0 - ratio) + bottom_rgb[0] * ratio)
        g = int(top_rgb[1] * (1.0 - ratio) + bottom_rgb[1] * ratio)
        b = int(top_rgb[2] * (1.0 - ratio) + bottom_rgb[2] * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    return img


def _measure(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> int:
    if not text:
        return 0
    left, _, right, _ = draw.textbbox((0, 0), text, font=font)
    return right - left


def _wrap_lines(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
    words = text.split()
    if not words:
        return []
    lines: list[str] = []
    line = words[0]
    for word in words[1:]:
        candidate = f"{line} {word}"
        if _measure(draw, candidate, font) <= max_width:
            line = candidate
        else:
            lines.append(line)
            line = word
    lines.append(line)
    return lines


def _truncate_lines(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    font: ImageFont.ImageFont,
    max_width: int,
    max_lines: int,
) -> list[str]:
    if len(lines) <= max_lines:
        return lines
    cut = lines[:max_lines]
    last = cut[-1]
    ellipsis = "..."
    while last and _measure(draw, last + ellipsis, font) > max_width:
        last = last[:-1]
    cut[-1] = (last.rstrip() + ellipsis) if last else ellipsis
    return cut


@lru_cache(maxsize=512)
def _render_cached(key: str, text: str, reference: str, lang: str) -> bytes:
    # Get Islamic background image
    image = _get_islamic_image()
    
    # Add semi-transparent overlay for text readability
    overlay = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT), (0, 0, 0, 140))
    image = image.convert("RGBA")
    image = Image.alpha_composite(image, overlay)
    image = image.convert("RGB")
    
    draw = ImageDraw.Draw(image)

    quote_font = _load_font(46 if lang == "tr" else 48)
    ref_font = _load_font(32)
    brand_font = _load_font(28)

    max_text_width = CARD_WIDTH - (MARGIN * 2)
    lines = _wrap_lines(draw, text.strip(), quote_font, max_text_width)
    lines = _truncate_lines(draw, lines, quote_font, max_text_width, max_lines=16)

    line_height = int((quote_font.size if hasattr(quote_font, "size") else 44) * 1.4)
    text_block_height = max(line_height * max(1, len(lines)), line_height)
    y = max(180, (CARD_HEIGHT - text_block_height) // 2 - 100)

    # Draw text with subtle shadow for depth
    for line in lines:
        w = _measure(draw, line, quote_font)
        x = (CARD_WIDTH - w) // 2
        # Shadow
        draw.text((x + 2, y + 2), line, fill=(0, 0, 0, 120), font=quote_font)
        # Main text
        draw.text((x, y), line, fill=TEXT_COLOR, font=quote_font)
        y += line_height

    ref_text = reference.strip()
    ref_lines = _truncate_lines(draw, _wrap_lines(draw, ref_text, ref_font, max_text_width), ref_font, max_text_width, max_lines=2)
    ref_y = CARD_HEIGHT - 240
    for line in ref_lines:
        w = _measure(draw, line, ref_font)
        x = (CARD_WIDTH - w) // 2
        # Shadow
        draw.text((x + 1, ref_y + 1), line, fill=(0, 0, 0, 100), font=ref_font)
        # Main text
        draw.text((x, ref_y), line, fill=REF_COLOR, font=ref_font)
        ref_y += int((ref_font.size if hasattr(ref_font, "size") else 30) * 1.3)

    # Brand watermark with decorative elements
    brand = "📿 Hadith Bot"
    bw = _measure(draw, brand, brand_font)
    draw.text(((CARD_WIDTH - bw) // 2, CARD_HEIGHT - 95), brand, fill=(200, 210, 220), font=brand_font)

    out = io.BytesIO()
    image.save(out, format="JPEG", quality=95, optimize=True)
    return out.getvalue()


def render_hadith_card(text: str, reference: str, lang: str) -> bytes:
    payload = f"{lang}\n{text}\n{reference}".encode("utf-8", errors="ignore")
    key = hashlib.sha256(payload).hexdigest()
    return _render_cached(key, text, reference, lang)


# --- LOCAL TESTING BLOCK ---
if __name__ == "__main__":
    print("Testing Hadith card generation...")
    
    test_hadith = "The most beloved of deeds to Allah are those that are most consistent, even if it is small."
    test_ref = "Sahih al-Bukhari 6464"
    test_lang = "en"
    
    try:
        # Generate the card using your local image cache
        image_bytes = render_hadith_card(test_hadith, test_ref, test_lang)
        
        # Save the raw bytes to an actual image file so you can look at it
        output_filename = "test_output.jpg"
        with open(output_filename, "wb") as f:
            f.write(image_bytes)
            
        print(f"✅ Success! Open '{output_filename}' in your project folder to see the result.")
    except Exception as e:
        print(f"❌ Error generating card: {e}")
