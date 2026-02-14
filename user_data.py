#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
💾 User Data Manager
Bookmarks, reading progress, streaks, language preferences,
and reminders — persisted in JSON.
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
            "reminders": [],
        }
    # Migrate: add reminders list if missing (for existing users)
    if "reminders" not in data[uid]:
        data[uid]["reminders"] = []
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


# ========================
# ⏰ REMINDERS
# ========================

def add_reminder(user_id, time_str: str, surah: int = None, ayah: int = None, label: str = "") -> dict:
    """
    Add a daily reminder.

    Args:
        user_id:  Telegram user ID
        time_str: Time in HH:MM format
        surah:    Optional: specific surah (None = random ayah)
        ayah:     Optional: specific ayah (None = random ayah)
        label:    Optional label / note

    Returns:
        The created reminder dict, or None if duplicate time.
    """
    data = _load_data()
    user = _get_user(data, user_id)

    # Check for duplicate time
    for r in user["reminders"]:
        if r["time"] == time_str:
            return None

    reminder = {
        "time": time_str,
        "surah": surah,
        "ayah": ayah,
        "label": label,
        "active": True,
    }
    user["reminders"].append(reminder)
    # Sort by time
    user["reminders"].sort(key=lambda r: r["time"])
    _save_data(data)
    return reminder


def remove_reminder(user_id, index: int) -> bool:
    """Remove a reminder by its 1-based index. Returns False if invalid."""
    data = _load_data()
    user = _get_user(data, user_id)

    if index < 1 or index > len(user["reminders"]):
        return False

    user["reminders"].pop(index - 1)
    _save_data(data)
    return True


def get_reminders(user_id) -> list:
    """Get all reminders for a user."""
    data = _load_data()
    user = _get_user(data, user_id)
    return user["reminders"]


def get_all_reminders() -> dict:
    """
    Get all reminders across ALL users.
    Returns: {user_id: [reminders]}
    """
    data = _load_data()
    result = {}
    for uid, user in data.items():
        reminders = user.get("reminders", [])
        if reminders:
            result[uid] = reminders
    return result


def toggle_reminder(user_id, index: int) -> bool | None:
    """Toggle a reminder on/off. Returns new state or None if invalid."""
    data = _load_data()
    user = _get_user(data, user_id)

    if index < 1 or index > len(user["reminders"]):
        return None

    reminder = user["reminders"][index - 1]
    reminder["active"] = not reminder["active"]
    _save_data(data)
    return reminder["active"]


def clear_reminders(user_id) -> int:
    """Remove all reminders. Returns count removed."""
    data = _load_data()
    user = _get_user(data, user_id)
    count = len(user["reminders"])
    user["reminders"] = []
    _save_data(data)
    return count
