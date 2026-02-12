#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
💾 User Data Manager
Bookmarks, reading progress, streaks, language preferences — persisted in JSON.
"""

import json
import os
from datetime import date

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_data.json")


# ========================
# 💾 PERSISTENCE
# ========================

def _load_data() -> dict:
    """Load all user data from JSON file."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def _save_data(data: dict):
    """Save user data to JSON file."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _get_user(data: dict, user_id) -> dict:
    """Get or create a user entry."""
    uid = str(user_id)
    if uid not in data:
        data[uid] = {
            "bookmarks": [],
            "read_ayahs": [],
            "language": "ru",
            "streak": 0,
            "last_active": None,
            "max_streak": 0,
        }
    return data[uid]


# ========================
# 🔖 BOOKMARKS
# ========================

def add_bookmark(user_id, surah: int, ayah: int) -> bool:
    """Add a bookmark. Returns False if already bookmarked."""
    data = _load_data()
    user = _get_user(data, user_id)
    ref = f"{surah}:{ayah}"

    if ref in user["bookmarks"]:
        return False

    user["bookmarks"].append(ref)
    _save_data(data)
    return True


def remove_bookmark(user_id, surah: int, ayah: int) -> bool:
    """Remove a bookmark. Returns False if not found."""
    data = _load_data()
    user = _get_user(data, user_id)
    ref = f"{surah}:{ayah}"

    if ref not in user["bookmarks"]:
        return False

    user["bookmarks"].remove(ref)
    _save_data(data)
    return True


def get_bookmarks(user_id) -> list:
    """Get all bookmarks for a user."""
    data = _load_data()
    user = _get_user(data, user_id)
    return user["bookmarks"]


# ========================
# 📊 READING PROGRESS
# ========================

def mark_ayah_read(user_id, surah: int, ayah: int):
    """Mark an ayah as read and update the daily streak."""
    data = _load_data()
    user = _get_user(data, user_id)
    ref = f"{surah}:{ayah}"

    if ref not in user["read_ayahs"]:
        user["read_ayahs"].append(ref)

    # Update streak
    today = date.today().isoformat()
    if user["last_active"] != today:
        yesterday = date.fromordinal(date.today().toordinal() - 1).isoformat()
        if user["last_active"] == yesterday:
            user["streak"] += 1
        else:
            user["streak"] = 1
        user["last_active"] = today
        user["max_streak"] = max(user.get("max_streak", 0), user["streak"])

    _save_data(data)


def get_reading_stats(user_id) -> dict:
    """Get reading statistics for a user."""
    data = _load_data()
    user = _get_user(data, user_id)
    total_read = len(user["read_ayahs"])
    total_ayahs = 6236

    return {
        "total_read": total_read,
        "total_ayahs": total_ayahs,
        "percentage": round((total_read / total_ayahs) * 100, 1) if total_ayahs > 0 else 0,
        "streak": user.get("streak", 0),
        "max_streak": user.get("max_streak", 0),
    }


def get_progress_bar(percentage: float, length: int = 20) -> str:
    """Generate a visual progress bar."""
    filled = int(length * percentage / 100)
    empty = length - filled
    bar = "█" * filled + "░" * empty
    return f"[{bar}] {percentage}%"


# ========================
# 🔥 STREAKS
# ========================

def get_streak(user_id) -> dict:
    """Get streak info for a user."""
    data = _load_data()
    user = _get_user(data, user_id)

    today = date.today().isoformat()
    streak = user.get("streak", 0)

    # Check if streak is still active (last active today or yesterday)
    last_active = user.get("last_active")
    if last_active:
        days_diff = (date.today() - date.fromisoformat(last_active)).days
        if days_diff > 1:
            streak = 0
            user["streak"] = 0
            _save_data(data)

    return {
        "current": streak,
        "max": user.get("max_streak", 0),
        "last_active": user.get("last_active"),
        "active_today": user.get("last_active") == today,
    }


# ========================
# 🌍 LANGUAGE PREFERENCE
# ========================

def set_language(user_id, lang: str):
    """Set user's preferred language."""
    data = _load_data()
    user = _get_user(data, user_id)
    user["language"] = lang
    _save_data(data)


def get_language(user_id) -> str:
    """Get user's preferred language. Default: 'ru'."""
    data = _load_data()
    user = _get_user(data, user_id)
    return user.get("language", "ru")
