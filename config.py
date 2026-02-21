#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
⚙️ Bot Configuration
Settings for the Hadith Telegram Bot (Sahih Bukhari)
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
# 🌍 LANGUAGE SETTINGS
# ========================

DEFAULT_LANGUAGE = "ru"

AVAILABLE_LANGUAGES = {
    "ru": "🇷🇺 Русский",
    "en": "🇬🇧 English",
    "tr": "🇹🇷 Türkçe",
}

# ========================
# 📡 HADITH API
# ========================

# fawazahmed0 Hadith CDN — individual section files (1-100)
# Each returns {metadata: {...}, hadiths: [{hadithnumber, text, grades, reference}]}
HADITH_API_BASE = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/eng-bukhari"
HADITH_SECTIONS = 100  # Sahih Bukhari has ~100 sections (books)

# ========================
# 🖼 IMAGE API (Pexels)
# ========================

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")
