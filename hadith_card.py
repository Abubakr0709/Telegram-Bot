#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Render hadith quote cards for Telegram photo messages.
"""

from __future__ import annotations

import hashlib
import io
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

CARD_WIDTH = 1080
CARD_HEIGHT = 1350
MARGIN = 88
TEXT_COLOR = (245, 245, 245)
REF_COLOR = (215, 220, 228)


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


def _vertical_gradient(
    width: int,
    height: int,
    top_rgb: tuple[int, int, int],
    bottom_rgb: tuple[int, int, int],
) -> Image.Image:
    img = Image.new("RGB", (width, height), top_rgb)
    draw = ImageDraw.Draw(img)
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
    image = _vertical_gradient(CARD_WIDTH, CARD_HEIGHT, (18, 33, 54), (10, 16, 30))
    draw = ImageDraw.Draw(image)

    quote_font = _load_font(42 if lang == "tr" else 44)
    ref_font = _load_font(30)
    brand_font = _load_font(26)

    max_text_width = CARD_WIDTH - (MARGIN * 2)
    lines = _wrap_lines(draw, text.strip(), quote_font, max_text_width)
    lines = _truncate_lines(draw, lines, quote_font, max_text_width, max_lines=16)

    line_height = int((quote_font.size if hasattr(quote_font, "size") else 40) * 1.35)
    text_block_height = max(line_height * max(1, len(lines)), line_height)
    y = max(160, (CARD_HEIGHT - text_block_height) // 2 - 120)

    for line in lines:
        w = _measure(draw, line, quote_font)
        x = (CARD_WIDTH - w) // 2
        draw.text((x, y), line, fill=TEXT_COLOR, font=quote_font)
        y += line_height

    ref_text = reference.strip()
    ref_lines = _truncate_lines(draw, _wrap_lines(draw, ref_text, ref_font, max_text_width), ref_font, max_text_width, max_lines=2)
    ref_y = CARD_HEIGHT - 220
    for line in ref_lines:
        w = _measure(draw, line, ref_font)
        x = (CARD_WIDTH - w) // 2
        draw.text((x, ref_y), line, fill=REF_COLOR, font=ref_font)
        ref_y += int((ref_font.size if hasattr(ref_font, "size") else 28) * 1.25)

    brand = "Hadith Bot"
    bw = _measure(draw, brand, brand_font)
    draw.text(((CARD_WIDTH - bw) // 2, CARD_HEIGHT - 90), brand, fill=(160, 170, 186), font=brand_font)

    out = io.BytesIO()
    image.save(out, format="JPEG", quality=92, optimize=True)
    return out.getvalue()


def render_hadith_card(text: str, reference: str, lang: str) -> bytes:
    payload = f"{lang}\n{text}\n{reference}".encode("utf-8", errors="ignore")
    key = hashlib.sha256(payload).hexdigest()
    return _render_cached(key, text, reference, lang)
