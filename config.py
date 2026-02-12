#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
⚙️ Bot Configuration
All settings for the Quran Tafsir Telegram Bot
"""

import os

# ========================
# 🤖 BOT CREDENTIALS
# ========================

BOT_TOKEN = "8500294939:AAHMCmTDOQRd3FtT2mqpO1IOLIFGvHs3ujk"
CHAT_ID = 7258913956

# ========================
# 📚 LOCAL TAFSIR PATHS
# ========================

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QURTUBI_PATH = os.path.join(_BASE_DIR, "ar-tafseer-al-qurtubi")
QUSHAIRI_PATH = os.path.join(_BASE_DIR, "en-al-qushairi-tafsir")

# Max chars of tafsir text before truncation (Telegram message limit ~4096)
MAX_TAFSIR_LENGTH = 1800

# ========================
# ⏰ SCHEDULE SETTINGS
# ========================

SCHEDULE_TIMES = [
    "00:00", "01:36", "03:12", "04:48", "06:24",
    "08:00", "09:36", "11:12", "12:48", "14:24",
    "16:00", "17:36", "19:12", "20:48", "22:24",
]

# ========================
# 🌍 LANGUAGE SETTINGS
# ========================

DEFAULT_LANGUAGE = "ru"
DEFAULT_TRANSLATION = "ru.kuliev"

AVAILABLE_TRANSLATIONS = {
    "ru": "🇷🇺 Русский",
    "en": "🇬🇧 English",
    "tr": "🇹🇷 Türkçe",
}

# Quran API translation editions per language
QURAN_EDITIONS = {
    "ru": "ru.kuliev",
    "en": "en.sahih",
    "tr": "tr.diyanet",
}

# ========================
# 📡 API ENDPOINTS
# ========================

QURAN_API_BASE = "https://api.alquran.cloud/v1"
HADITH_API = "https://random-hadith-generator.vercel.app/bukhari/"
