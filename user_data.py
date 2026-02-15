#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
💾 User Data Manager
Bookmarks and reading tracking — persisted in JSON.
Simplified: no reminders, no language prefs, no streaks.
"""

import json
import os

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
        }
    return data[uid]


# ========================
# 👤 USER EXISTENCE
# ========================

def user_exists(user_id) -> bool:
    """Check if user already has a record."""
    data = _load_data()
    return str(user_id) in data


def ensure_user(user_id):
    """Create user record if it doesn't exist."""
    data = _load_data()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {
            "bookmarks": [],
            "read_ayahs": [],
        }
        _save_data(data)


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
# 📊 READING TRACKING
# ========================

def mark_ayah_read(user_id, surah: int, ayah: int):
    """Mark an ayah as read."""
    data = _load_data()
    user = _get_user(data, user_id)
    ref = f"{surah}:{ayah}"

    if ref not in user["read_ayahs"]:
        user["read_ayahs"].append(ref)
        _save_data(data)
