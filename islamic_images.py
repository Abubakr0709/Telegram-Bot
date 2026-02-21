#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Islamic photo provider using Pexels API.
Returns high-quality background image URLs suitable for Telegram posts.
"""

from __future__ import annotations

import random
from typing import Any

import requests

PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"

_QUERIES = [
    "islamic mosque architecture",
    "mosque interior islamic",
    "quran islamic calligraphy",
    "islamic geometric pattern",
    "masjid dome minaret",
]

_FALLBACK_IMAGES = [
    "https://images.pexels.com/photos/1619317/pexels-photo-1619317.jpeg?auto=compress&cs=tinysrgb&h=2160&w=3840",
    "https://images.pexels.com/photos/724916/pexels-photo-724916.jpeg?auto=compress&cs=tinysrgb&h=2160&w=3840",
    "https://images.pexels.com/photos/2781760/pexels-photo-2781760.jpeg?auto=compress&cs=tinysrgb&h=2160&w=3840",
    "https://images.pexels.com/photos/2087391/pexels-photo-2087391.jpeg?auto=compress&cs=tinysrgb&h=2160&w=3840",
]


def _is_high_quality(photo: dict[str, Any]) -> bool:
    width = int(photo.get("width", 0))
    height = int(photo.get("height", 0))
    # Require at least 4K on one side and decent size on the other.
    return max(width, height) >= 3840 and min(width, height) >= 2000


def fetch_islamic_photo_url(api_key: str, query: str | None = None) -> str | None:
    """Fetch a high-quality Islamic photo URL from Pexels."""
    if not api_key:
        return random.choice(_FALLBACK_IMAGES)

    q = query or random.choice(_QUERIES)
    headers = {"Authorization": api_key}
    params = {
        "query": q,
        "per_page": 40,
        "page": random.randint(1, 5),
        "orientation": "landscape",
        "size": "large",
    }

    try:
        resp = requests.get(PEXELS_SEARCH_URL, headers=headers, params=params, timeout=12)
        resp.raise_for_status()
        photos = resp.json().get("photos", [])
    except Exception:
        return None

    picks = [p for p in photos if _is_high_quality(p)]
    if not picks:
        picks = photos
    if not picks:
        return random.choice(_FALLBACK_IMAGES)

    chosen = random.choice(picks)
    src = chosen.get("src", {})
    # Prefer original for quality, fallback to large2x if needed.
    return src.get("original") or src.get("large2x") or src.get("large") or random.choice(_FALLBACK_IMAGES)
