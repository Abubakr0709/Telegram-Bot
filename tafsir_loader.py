#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
📚 Local Tafsir Loader
Reads tafsir from local JSON files:
  - ar-tafseer-al-qurtubi/ (Arabic classical tafsir by Imam al-Qurtubi)
  - en-al-qushairi-tafsir/ (English spiritual tafsir by al-Qushairi)

No external APIs are used for tafsir.
"""

import json
import os
from config import QURTUBI_PATH, QUSHAIRI_PATH, MAX_TAFSIR_LENGTH

# ========================
# 📂 SOURCE PATHS
# ========================

SOURCES = {
    "qurtubi": QURTUBI_PATH,
    "qushairi": QUSHAIRI_PATH,
}

# ========================
# 📖 SURAH METADATA
# ========================

SURAH_NAMES = {
    1: "الفاتحة", 2: "البقرة", 3: "آل عمران", 4: "النساء", 5: "المائدة",
    6: "الأنعام", 7: "الأعراف", 8: "الأنفال", 9: "التوبة", 10: "يونس",
    11: "هود", 12: "يوسف", 13: "الرعد", 14: "إبراهيم", 15: "الحجر",
    16: "النحل", 17: "الإسراء", 18: "الكهف", 19: "مريم", 20: "طه",
    21: "الأنبياء", 22: "الحج", 23: "المؤمنون", 24: "النور", 25: "الفرقان",
    26: "الشعراء", 27: "النمل", 28: "القصص", 29: "العنكبوت", 30: "الروم",
    31: "لقمان", 32: "السجدة", 33: "الأحزاب", 34: "سبأ", 35: "فاطر",
    36: "يس", 37: "الصافات", 38: "ص", 39: "الزمر", 40: "غافر",
    41: "فصلت", 42: "الشورى", 43: "الزخرف", 44: "الدخان", 45: "الجاثية",
    46: "الأحقاف", 47: "محمد", 48: "الفتح", 49: "الحجرات", 50: "ق",
    51: "الذاريات", 52: "الطور", 53: "النجم", 54: "القمر", 55: "الرحمن",
    56: "الواقعة", 57: "الحديد", 58: "المجادلة", 59: "الحشر", 60: "الممتحنة",
    61: "الصف", 62: "الجمعة", 63: "المنافقون", 64: "التغابن", 65: "الطلاق",
    66: "التحريم", 67: "الملك", 68: "القلم", 69: "الحاقة", 70: "المعارج",
    71: "نوح", 72: "الجن", 73: "المزمل", 74: "المدثر", 75: "القيامة",
    76: "الإنسان", 77: "المرسلات", 78: "النبأ", 79: "النازعات", 80: "عبس",
    81: "التكوير", 82: "الانفطار", 83: "المطففين", 84: "الانشقاق", 85: "البروج",
    86: "الطارق", 87: "الأعلى", 88: "الغاشية", 89: "الفجر", 90: "البلد",
    91: "الشمس", 92: "الليل", 93: "الضحى", 94: "الشرح", 95: "التين",
    96: "العلق", 97: "القدر", 98: "البينة", 99: "الزلزلة", 100: "العاديات",
    101: "القارعة", 102: "التكاثر", 103: "العصر", 104: "الهمزة", 105: "الفيل",
    106: "قريش", 107: "الماعون", 108: "الكوثر", 109: "الكافرون", 110: "النصر",
    111: "المسد", 112: "الإخلاص", 113: "الفلق", 114: "الناس",
}

SURAH_AYAH_COUNT = {
    1: 7, 2: 286, 3: 200, 4: 176, 5: 120, 6: 165, 7: 206, 8: 75,
    9: 129, 10: 109, 11: 123, 12: 111, 13: 43, 14: 52, 15: 99,
    16: 128, 17: 111, 18: 110, 19: 98, 20: 135, 21: 112, 22: 78,
    23: 118, 24: 64, 25: 77, 26: 227, 27: 93, 28: 88, 29: 69, 30: 60,
    31: 34, 32: 30, 33: 73, 34: 54, 35: 45, 36: 83, 37: 182, 38: 88,
    39: 75, 40: 85, 41: 54, 42: 53, 43: 89, 44: 59, 45: 37, 46: 35,
    47: 38, 48: 29, 49: 18, 50: 45, 51: 60, 52: 49, 53: 62, 54: 55,
    55: 78, 56: 96, 57: 29, 58: 22, 59: 24, 60: 13, 61: 14, 62: 11,
    63: 11, 64: 18, 65: 12, 66: 12, 67: 30, 68: 52, 69: 52, 70: 44,
    71: 28, 72: 28, 73: 20, 74: 56, 75: 40, 76: 31, 77: 50, 78: 40,
    79: 46, 80: 42, 81: 29, 82: 19, 83: 36, 84: 25, 85: 22, 86: 17,
    87: 19, 88: 26, 89: 30, 90: 20, 91: 15, 92: 21, 93: 11, 94: 8,
    95: 8, 96: 19, 97: 5, 98: 8, 99: 8, 100: 11, 101: 11, 102: 8,
    103: 3, 104: 9, 105: 5, 106: 4, 107: 7, 108: 3, 109: 6, 110: 3,
    111: 5, 112: 4, 113: 5, 114: 6,
}

TOTAL_AYAHS = 6236


# ========================
# 🔧 HELPERS
# ========================

def _get_source_path(source: str) -> str:
    """Get the filesystem path for a tafsir source."""
    if source not in SOURCES:
        raise ValueError(f"Unknown source: {source}. Use 'qurtubi' or 'qushairi'.")
    return SOURCES[source]


def _truncate_text(text: str, max_length: int = None) -> str:
    """Truncate text to max_length, ending at a sentence boundary if possible."""
    if max_length is None:
        max_length = MAX_TAFSIR_LENGTH
    if len(text) <= max_length:
        return text

    truncated = text[:max_length]
    # Try to end at a sentence boundary
    last_period = max(truncated.rfind(". "), truncated.rfind("。"), truncated.rfind("؟"))
    if last_period > max_length * 0.5:
        truncated = truncated[: last_period + 1]

    return truncated + " (...)"


# ========================
# 📖 TAFSIR LOADING
# ========================

def get_tafsir_for_ayah(surah_num: int, ayah_num: int, source: str = "qurtubi") -> str:
    """
    Load tafsir text for a specific ayah from local JSON files.

    Lookup order:
      1. Per-ayah file: {source_path}/{surah}/{ayah}.json
      2. Surah-level file: {source_path}/{surah}.json  → search ayahs array

    Args:
        surah_num: Surah number (1-114)
        ayah_num:  Ayah number within the surah
        source:    "qurtubi" (Arabic) or "qushairi" (English)

    Returns:
        Tafsir text string, truncated to MAX_TAFSIR_LENGTH.
        Falls back to a "not found" message.
    """
    base_path = _get_source_path(source)

    # 1) Try per-ayah file: {surah}/{ayah}.json
    ayah_file = os.path.join(base_path, str(surah_num), f"{ayah_num}.json")
    if os.path.exists(ayah_file):
        try:
            with open(ayah_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                text = data.get("text", "")
                if text:
                    return _truncate_text(text)
        except (json.JSONDecodeError, KeyError):
            pass

    # 2) Fallback: surah-level file {surah}.json
    surah_file = os.path.join(base_path, f"{surah_num}.json")
    if os.path.exists(surah_file):
        try:
            with open(surah_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for ayah in data.get("ayahs", []):
                    if ayah.get("ayah") == ayah_num:
                        text = ayah.get("text", "")
                        if text:
                            return _truncate_text(text)
        except (json.JSONDecodeError, KeyError):
            pass

    return "Тафсир не найден для этого аята."


# ========================
# 🔍 SEARCH
# ========================

def search_tafsir(keyword: str, source: str = "qushairi", max_results: int = 10) -> list:
    """
    Search tafsir texts for a keyword across all surahs.

    Args:
        keyword:     Search term (case-insensitive)
        source:      "qurtubi" or "qushairi"
        max_results: Maximum number of results

    Returns:
        List of dicts: [{surah, ayah, snippet, surah_name}]
    """
    base_path = _get_source_path(source)
    results = []
    keyword_lower = keyword.lower()

    for surah_num in range(1, 115):
        if len(results) >= max_results:
            break

        surah_file = os.path.join(base_path, f"{surah_num}.json")
        if not os.path.exists(surah_file):
            continue

        try:
            with open(surah_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for ayah in data.get("ayahs", []):
                    if len(results) >= max_results:
                        break

                    text = ayah.get("text", "")
                    if keyword_lower in text.lower():
                        idx = text.lower().find(keyword_lower)
                        start = max(0, idx - 60)
                        end = min(len(text), idx + len(keyword) + 60)
                        snippet = (
                            ("..." if start > 0 else "")
                            + text[start:end]
                            + ("..." if end < len(text) else "")
                        )
                        results.append({
                            "surah": ayah.get("surah", surah_num),
                            "ayah": ayah.get("ayah"),
                            "snippet": snippet,
                            "surah_name": SURAH_NAMES.get(surah_num, f"Surah {surah_num}"),
                        })
        except (json.JSONDecodeError, KeyError):
            continue

    return results


# ========================
# 📌 NAVIGATION HELPERS
# ========================

def get_surah_name(surah_num: int) -> str:
    """Get Arabic surah name."""
    return SURAH_NAMES.get(surah_num, f"سورة {surah_num}")


def get_ayah_count(surah_num: int) -> int:
    """Get total number of ayahs in a surah."""
    return SURAH_AYAH_COUNT.get(surah_num, 0)


def get_next_ayah(surah_num: int, ayah_num: int) -> tuple:
    """Get next ayah reference (surah, ayah). Wraps to next surah."""
    max_ayahs = get_ayah_count(surah_num)
    if ayah_num < max_ayahs:
        return (surah_num, ayah_num + 1)
    elif surah_num < 114:
        return (surah_num + 1, 1)
    else:
        return (1, 1)


def get_prev_ayah(surah_num: int, ayah_num: int) -> tuple:
    """Get previous ayah reference (surah, ayah). Wraps to prev surah."""
    if ayah_num > 1:
        return (surah_num, ayah_num - 1)
    elif surah_num > 1:
        prev_surah = surah_num - 1
        return (prev_surah, get_ayah_count(prev_surah))
    else:
        return (114, get_ayah_count(114))
