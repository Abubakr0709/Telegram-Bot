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

BOT_TOKEN = os.environ.get(
    "BOT_TOKEN",
    "8500294939:AAHMCmTDOQRd3FtT2mqpO1IOLIFGvHs3ujk",
)
CHAT_ID = int(os.environ.get("CHAT_ID", "7258913956"))

# ========================
# 📚 LOCAL TAFSIR PATHS
# ========================

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QURTUBI_PATH = os.path.join(_BASE_DIR, "ar-tafseer-al-qurtubi")
QUSHAIRI_PATH = os.path.join(_BASE_DIR, "en-al-qushairi-tafsir")

# Max chars of tafsir in Telegram messages (full text served via web app)
MAX_TAFSIR_LENGTH = 1800

# ========================
# 🌐 WEB APP SETTINGS
# ========================

# The HTTPS URL where the bot's web server is reachable by Telegram.
# For local dev with ngrok:  https://xxxx.ngrok-free.app
# For Render / Railway:      https://your-app.onrender.com
WEBAPP_URL = os.environ.get("WEBAPP_URL", "http://127.0.0.1:5000")

# Flask server settings (runs inside main.py alongside the bot)
FLASK_HOST = os.environ.get("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.environ.get("FLASK_PORT", "5000"))

# ========================
# ⏰ SCHEDULE SETTINGS
# ========================

# 10 scheduled daily ayah messages
SCHEDULE_TIMES = [
    "06:00", "08:24", "10:48", "13:12", "15:36",
    "18:00", "19:30", "21:00", "22:30", "23:50",
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

QURAN_EDITIONS = {
    "ru": "ru.kuliev",
    "en": "en.sahih",
    "tr": "tr.diyanet",
}

# ========================
# 📡 API ENDPOINTS
# ========================

QURAN_API_BASE = "https://api.alquran.cloud/v1"

# fawazahmed0 Hadith CDN — individual section files (1-100)
# Each returns {metadata: {...}, hadiths: [{hadithnumber, text, grades, reference}]}
HADITH_API_BASE = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/eng-bukhari"
HADITH_SECTIONS = 100  # Sahih Bukhari has ~100 sections (books)
