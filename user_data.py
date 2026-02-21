#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
💾 User Data Manager
Favorites, daily hadith settings, language preferences,
persisted in JSON.
"""

import json
import os

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_data.json")


# ========================
# 💾 PERSISTENCE
# ========================

def _load_data() -> dict:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def _save_data(data: dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _get_user(data: dict, user_id) -> dict:
    uid = str(user_id)
    if uid not in data:
        data[uid] = {
            "language": "ru",
            "favorites": [],
            "daily_time": None,      # HH:MM or None
            "daily_index": 0,        # sequential hadith counter
        }
    # Migrate existing users — add missing keys
    u = data[uid]
    u.setdefault("favorites", [])
    u.setdefault("daily_time", None)
    u.setdefault("daily_index", 0)
    return u


# ========================
# 🌍 LANGUAGE PREFERENCE
# ========================

def set_language(user_id, lang: str):
    data = _load_data()
    user = _get_user(data, user_id)
    user["language"] = lang
    _save_data(data)


def get_language(user_id) -> str:
    data = _load_data()
    user = _get_user(data, user_id)
    return user.get("language", "ru")


# ========================
# ⭐ FAVORITES
# ========================

def add_favorite(user_id, text: str, reference: str) -> dict | None:
    """Save a hadith as a favorite. Returns the new entry or None if duplicate."""
    data = _load_data()
    user = _get_user(data, user_id)

    # Deduplicate by reference
    for fav in user["favorites"]:
        if fav["reference"] == reference:
            return None

    fav_id = (max((f["id"] for f in user["favorites"]), default=0)) + 1
    entry = {"id": fav_id, "text": text, "reference": reference}
    user["favorites"].append(entry)
    _save_data(data)
    return entry


def remove_favorite(user_id, fav_id: int) -> bool:
    """Remove a favorite by its id. Returns False if not found."""
    data = _load_data()
    user = _get_user(data, user_id)
    before = len(user["favorites"])
    user["favorites"] = [f for f in user["favorites"] if f["id"] != fav_id]
    if len(user["favorites"]) < before:
        _save_data(data)
        return True
    return False


def get_favorites(user_id) -> list:
    data = _load_data()
    user = _get_user(data, user_id)
    return user["favorites"]


# ========================
# 📅 DAILY HADITH
# ========================

def set_daily_time(user_id, time_str: str):
    """Set the daily hadith delivery time (HH:MM)."""
    data = _load_data()
    user = _get_user(data, user_id)
    user["daily_time"] = time_str
    _save_data(data)


def get_daily_time(user_id) -> str | None:
    data = _load_data()
    user = _get_user(data, user_id)
    return user.get("daily_time")


def disable_daily(user_id):
    data = _load_data()
    user = _get_user(data, user_id)
    user["daily_time"] = None
    _save_data(data)


def get_daily_index(user_id) -> int:
    data = _load_data()
    user = _get_user(data, user_id)
    return user.get("daily_index", 0)


def increment_daily_index(user_id):
    data = _load_data()
    user = _get_user(data, user_id)
    user["daily_index"] = user.get("daily_index", 0) + 1
    _save_data(data)


def get_all_daily_users() -> dict:
    """Returns {uid: daily_time} for all users with daily enabled."""
    data = _load_data()
    return {
        uid: u["daily_time"]
        for uid, u in data.items()
        if u.get("daily_time")
    }

# ========================
# 🗃 LAST HADITH (for /fav)
# ========================

def set_last_hadith(user_id, text: str, reference: str):
    """Remember the last hadith shown to this user (for /fav)."""
    data = _load_data()
    user = _get_user(data, user_id)
    user["last_hadith"] = {"text": text, "reference": reference}
    _save_data(data)


def get_last_hadith(user_id) -> dict | None:
    data = _load_data()
    user = _get_user(data, user_id)
    return user.get("last_hadith")
