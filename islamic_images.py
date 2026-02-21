#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Islamic photo provider using Pexels API.
Returns high-quality background image URLs suitable for Telegram posts.
"""

from __future__ import annotations

import random
from collections import deque
from typing import Any

import requests

PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"
MIN_WIDTH = 2048
MIN_HEIGHT = 2048

_QUERIES = [
    "islam quran mosque prayer",
    "quran islamic calligraphy arabic",
    "muslim prayer mosque interior",
    "masjid mihrab minbar islamic",
    "islamic architecture mosque dome minaret",
    "islamic geometric arabesque pattern",
    "ramadan quran mosque",
    "eid prayer mosque",
]

_FALLBACK_IMAGES = [
    "https://images.pexels.com/photos/1619317/pexels-photo-1619317.jpeg?auto=compress&cs=tinysrgb&h=2160&w=3840",
    "https://images.pexels.com/photos/724916/pexels-photo-724916.jpeg?auto=compress&cs=tinysrgb&h=2160&w=3840",
    "https://images.pexels.com/photos/2781760/pexels-photo-2781760.jpeg?auto=compress&cs=tinysrgb&h=2160&w=3840",
    "https://images.pexels.com/photos/2087391/pexels-photo-2087391.jpeg?auto=compress&cs=tinysrgb&h=2160&w=3840",
]

_RECENT_URLS: deque[str] = deque(maxlen=40)

_RELIGIOUS_HINTS = {
    "islam", "islamic", "muslim", "mosque", "masjid", "quran", "koran",
    "allah", "ramadan", "eid", "prayer", "salah", "dua", "tasbih",
    "calligraphy", "arabic", "mihrab", "minbar", "minaret", "dome",
    "kaaba", "makkah", "mecca", "madinah", "medina", "hijab",
}

_NON_RELIGIOUS_HINTS = {
    "mountain", "forest", "waterfall", "beach", "ocean", "river", "sunset",
    "landscape", "nature", "tree", "flower", "cityscape", "sky", "cloud",
    "road", "car", "animal", "wildlife", "food",
}


def _is_high_quality(photo: dict[str, Any]) -> bool:
    width = int(photo.get("width", 0))
    height = int(photo.get("height", 0))
    return width >= MIN_WIDTH and height >= MIN_HEIGHT


def _looks_islamic(photo: dict[str, Any]) -> bool:
    alt = str(photo.get("alt", "")).lower()
    if not alt:
        return False
    has_religious = any(k in alt for k in _RELIGIOUS_HINTS)
    has_non_religious = any(k in alt for k in _NON_RELIGIOUS_HINTS)
    return has_religious and not has_non_religious


def _remember_and_pick(urls: list[str]) -> str | None:
    if not urls:
        return None
    uniq = list(dict.fromkeys(urls))
    fresh = [u for u in uniq if u not in _RECENT_URLS]
    pool = fresh or uniq
    picked = random.choice(pool)
    _RECENT_URLS.append(picked)
    return picked


def _query_pexels(api_key: str, query: str, page: int) -> list[str]:
    headers = {"Authorization": api_key}
    params = {
        "query": query,
        "per_page": 80,
        "page": page,
        "orientation": random.choice(["landscape", "portrait"]),
        "size": "large",
    }
    try:
        resp = requests.get(PEXELS_SEARCH_URL, headers=headers, params=params, timeout=12)
        resp.raise_for_status()
        photos = resp.json().get("photos", [])
    except Exception:
        return []

    results: list[str] = []
    for p in photos:
        if not _is_high_quality(p):
            continue
        if not _looks_islamic(p):
            continue
        src = p.get("src", {})
        url = src.get("original") or src.get("large2x") or src.get("large")
        if url:
            results.append(url)
    return results


def fetch_islamic_photo_url(api_key: str, query: str | None = None) -> str | None:
    """Fetch a non-repeating Islamic photo URL (>=2K) from Pexels."""
    if not api_key:
        return _remember_and_pick(_FALLBACK_IMAGES)

    merged: list[str] = []
    attempts = 4
    for _ in range(attempts):
        q = query or random.choice(_QUERIES)
        page = random.randint(1, 30)
        merged.extend(_query_pexels(api_key, q, page))

    picked = _remember_and_pick(merged)
    if picked:
        return picked
    return _remember_and_pick(_FALLBACK_IMAGES)
