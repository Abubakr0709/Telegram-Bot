#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🕌 Quran & Tafsir Telegram Bot  (all-in-one)
──────────────────────────────────────────────
Runs BOTH the Telegram bot AND the Flask web server
in a single process so one `python main.py` starts everything.

Translation: deep-translator (Google Translate) with disk cache.
Full i18n: every bot message adapts to the user's chosen language.
"""

import asyncio
import hashlib
import json
import logging
import os
import random
import threading
import time as _time

import requests
from deep_translator import GoogleTranslator
from flask import Flask, jsonify, request as flask_request, send_from_directory
from flask_cors import CORS
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import (
    BOT_TOKEN,
    CHAT_ID,
    SCHEDULE_TIMES,
    AVAILABLE_TRANSLATIONS,
    QURAN_API_BASE,
    HADITH_API_BASE,
    HADITH_SECTIONS,
    QURAN_EDITIONS,
    DEFAULT_TRANSLATION,
    WEBAPP_URL,
    FLASK_HOST,
    FLASK_PORT,
)
from tafsir_loader import (
    get_tafsir_for_ayah,
    get_full_tafsir,
    search_tafsir,
    get_surah_name,
    get_ayah_count,
    get_next_ayah,
    get_prev_ayah,
    SURAH_NAMES,
    SURAH_AYAH_COUNT,
)
import user_data

# ═══════════════════════════════════════════
# 📝  LOGGING
# ═══════════════════════════════════════════

logging.basicConfig(
    format="%(asctime)s  %(name)-18s  %(levelname)-7s  %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("bot")
logging.getLogger("werkzeug").setLevel(logging.WARNING)

# ═══════════════════════════════════════════
# 🌍  FULL  i18n  STRINGS
# ═══════════════════════════════════════════

_STRINGS = {
    "ru": {
        "title": "КОРАН И ТАФСИР",
        "arabic_label": "Арабский текст",
        "translation_label": "Перевод",
        "hadith_label": "Хадис дня",
        "tafsir_btn": "📖 Читать полный Тафсир",
        "bookmark_btn": "🔖 Закладка",
        "more_hadith": "🔄 Ещё хадис",
        "translate_btn": "🌐 Перевести",
        "surah_word": "Сура",
        "ayah_word": "Аят",
        "full_tafsir_hint": "👇 Нажмите кнопку для полного тафсира",
        "blessing": "🤲 Да благословит вас Аллах знанием.",
        "loading": "📖 Загружаю аят… ✨",
        "load_error": "❌ Ошибка загрузки. Попробуйте ещё раз.",
        "welcome": (
            "✨ <b>Ас-саляму алейкум!</b> ✨\n\n"
            "Добро пожаловать в <b>Коран и Тафсир Бот</b>! 🕌\n\n"
            "📅 <b>Возможности:</b>\n"
            "  • Аят + тафсир + хадис каждый день\n"
            "  • 📖 Mini App для полного тафсира\n"
            "  • ⏰ Личные напоминания\n"
            "  • 🇷🇺 🇬🇧 🇹🇷 Перевод (Google)\n"
            "  • ⬅️ ➡️ Навигация по аятам\n"
            "  • 🔍 Поиск · 🔖 Закладки\n\n"
            "🎮 <b>Команды:</b>\n"
            "/now — Аят прямо сейчас\n"
            "/ayah 2:255 — Конкретный аят\n"
            "/hadith — Случайный хадис\n"
            "/remind 08:30 — Добавить напоминание\n"
            "/reminders — Мои напоминания\n"
            "/search слово — Поиск в тафсирах\n"
            "/bookmark 2:255 — Закладка\n"
            "/bookmarks — Мои закладки\n\n"
            "🤲 <i>Пусть этот бот приблизит вас к словам Аллаха.</i>"
        ),
        "streak_days": "дн.",
        "streak_label": "Серия",
        "qurtubi_excerpt": "Тафсир аль-Куртуби (отрывок)",
        "qushairi_excerpt": "Тафсир аль-Кушайри (отрывок)",
        "full_text_hint": "👇 Полный текст — кнопка ниже",
        "ayah_usage": "📌 <b>Формат:</b> <code>/ayah 2:255</code>",
        "ayah_bad_format": "❌ Неверный формат. <code>/ayah 2:255</code>",
        "hadith_title": "📿 <b>Хадис</b>",
        "search_hint": "🔍 <code>/search слово</code> — поиск в тафсире",
        "searching": "🔍 Ищу «{kw}»…",
        "search_empty": "😔 По запросу «{kw}» ничего не найдено.",
        "search_results": "🔍 <b>Результаты: «{kw}»</b> ({n})",
        "bookmark_usage": "🔖 <code>/bookmark 2:255</code>",
        "bookmark_bad": "❌ Формат: <code>/bookmark 2:255</code>",
        "bookmark_added": "✅ <b>Закладка:</b> {name} — {ref}",
        "bookmark_dup": "📌 Уже в закладках!",
        "bookmarks_empty": "📌 Нет закладок. <code>/bookmark 2:255</code>",
        "bookmarks_title": "🔖 <b>Ваши закладки:</b>",
        "remind_help": (
            "⏰ <b>Формат:</b>\n\n"
            "<code>/remind 08:30</code> — случайный аят\n"
            "<code>/remind 08:30 2:255</code> — конкретный аят\n"
            "<code>/remind 08:30 Утро</code> — с подписью\n\n"
            "Удалить: /reminders → /delremind номер"
        ),
        "remind_bad_time": "❌ Формат: <code>HH:MM</code>",
        "remind_dup": "⚠️ Уже есть на {t}.",
        "remind_ok": "✅ <b>Напоминание:</b> {t}  •  {desc}\n/reminders",
        "random_ayah": "случайный аят",
        "reminders_empty": "⏰ Нет напоминаний. <code>/remind 08:30</code>",
        "reminders_title": "⏰ <b>Ваши напоминания:</b>",
        "delremind_help": "<code>/delremind 1</code> или <code>/delremind all</code>",
        "deleted_n": "🗑️ Удалено: {n}.",
        "deleted_ok": "✅ #{i} удалено.",
        "deleted_bad": "❌ Нет #{i}. /reminders",
        "reminder_msg": "⏰ <b>Напоминание</b>",
        "msg_truncated": "\n\n⚠️ <i>Сообщение сокращено.</i>",
        "reflections": [
            "💭 Каждый аят — послание именно для вас в этот момент.",
            "💭 Коран — зеркало души. Что вы видите сегодня?",
            "💭 Истинное знание приходит через размышление.",
            "💭 Пусть каждое слово Аллаха станет светом на вашем пути.",
            "💭 Терпение и благодарность — два крыла верующего.",
            "💭 Каждый день — возможность стать ближе к Аллаху.",
            "💭 Мудрость Корана раскрывается тем, кто ищет сердцем.",
            "💭 В тишине размышления рождается понимание.",
            "💭 Аллах не обременяет душу сверх её возможностей.",
            "💭 Пусть сегодняшний аят станет проводником на весь день.",
        ],
    },
    "en": {
        "title": "QURAN & TAFSIR",
        "arabic_label": "Arabic Text",
        "translation_label": "Translation",
        "hadith_label": "Hadith of the Day",
        "tafsir_btn": "📖 Read Full Tafsir",
        "bookmark_btn": "🔖 Bookmark",
        "more_hadith": "🔄 Another hadith",
        "translate_btn": "🌐 Translate",
        "surah_word": "Surah",
        "ayah_word": "Ayah",
        "full_tafsir_hint": "👇 Tap the button below for full tafsir",
        "blessing": "🤲 May Allah bless you with knowledge.",
        "loading": "📖 Loading ayah… ✨",
        "load_error": "❌ Failed to load. Try again.",
        "welcome": (
            "✨ <b>As-salamu alaykum!</b> ✨\n\n"
            "Welcome to the <b>Quran & Tafsir Bot</b>! 🕌\n\n"
            "📅 <b>Features:</b>\n"
            "  • Daily ayah + tafsir + hadith\n"
            "  • 📖 Mini App for full tafsir\n"
            "  • ⏰ Personal reminders\n"
            "  • 🇷🇺 🇬🇧 🇹🇷 Translation (Google)\n"
            "  • ⬅️ ➡️ Ayah navigation\n"
            "  • 🔍 Search · 🔖 Bookmarks\n\n"
            "🎮 <b>Commands:</b>\n"
            "/now — Random ayah now\n"
            "/ayah 2:255 — Specific ayah\n"
            "/hadith — Random hadith\n"
            "/remind 08:30 — Add reminder\n"
            "/reminders — My reminders\n"
            "/search word — Search tafsir\n"
            "/bookmark 2:255 — Bookmark\n"
            "/bookmarks — My bookmarks\n\n"
            "🤲 <i>May this bot bring you closer to the words of Allah.</i>"
        ),
        "streak_days": "d",
        "streak_label": "Streak",
        "qurtubi_excerpt": "Tafsir al-Qurtubi (excerpt)",
        "qushairi_excerpt": "Tafsir al-Qushairi (excerpt)",
        "full_text_hint": "👇 Full text — button below",
        "ayah_usage": "📌 <b>Usage:</b> <code>/ayah 2:255</code>",
        "ayah_bad_format": "❌ Invalid format. <code>/ayah 2:255</code>",
        "hadith_title": "📿 <b>Hadith</b>",
        "search_hint": "🔍 <code>/search word</code> — search tafsir",
        "searching": "🔍 Searching «{kw}»…",
        "search_empty": "😔 No results for «{kw}».",
        "search_results": "🔍 <b>Results: «{kw}»</b> ({n})",
        "bookmark_usage": "🔖 <code>/bookmark 2:255</code>",
        "bookmark_bad": "❌ Format: <code>/bookmark 2:255</code>",
        "bookmark_added": "✅ <b>Bookmarked:</b> {name} — {ref}",
        "bookmark_dup": "📌 Already bookmarked!",
        "bookmarks_empty": "📌 No bookmarks yet. <code>/bookmark 2:255</code>",
        "bookmarks_title": "🔖 <b>Your bookmarks:</b>",
        "remind_help": (
            "⏰ <b>Usage:</b>\n\n"
            "<code>/remind 08:30</code> — random ayah\n"
            "<code>/remind 08:30 2:255</code> — specific ayah\n"
            "<code>/remind 08:30 Morning</code> — with label\n\n"
            "Delete: /reminders → /delremind number"
        ),
        "remind_bad_time": "❌ Format: <code>HH:MM</code>",
        "remind_dup": "⚠️ Already have a reminder at {t}.",
        "remind_ok": "✅ <b>Reminder:</b> {t}  •  {desc}\n/reminders",
        "random_ayah": "random ayah",
        "reminders_empty": "⏰ No reminders. <code>/remind 08:30</code>",
        "reminders_title": "⏰ <b>Your reminders:</b>",
        "delremind_help": "<code>/delremind 1</code> or <code>/delremind all</code>",
        "deleted_n": "🗑️ Deleted: {n}.",
        "deleted_ok": "✅ #{i} deleted.",
        "deleted_bad": "❌ No #{i}. /reminders",
        "reminder_msg": "⏰ <b>Reminder</b>",
        "msg_truncated": "\n\n⚠️ <i>Message truncated.</i>",
        "reflections": [
            "💭 Every ayah is a message meant for you at this very moment.",
            "💭 The Quran is a mirror of the soul. What do you see today?",
            "💭 True knowledge comes through reflection.",
            "💭 May every word of Allah illuminate your path.",
            "💭 Patience and gratitude — the two wings of a believer.",
            "💭 Every day is a chance to draw closer to Allah.",
            "💭 The wisdom of the Quran reveals itself to those who seek with their heart.",
            "💭 In the silence of contemplation, understanding is born.",
            "💭 Allah does not burden a soul beyond its capacity.",
            "💭 May today's ayah be a guiding light for your entire day.",
        ],
    },
    "tr": {
        "title": "KUR'AN VE TEFSİR",
        "arabic_label": "Arapça Metin",
        "translation_label": "Çeviri",
        "hadith_label": "Günün Hadisi",
        "tafsir_btn": "📖 Tam Tefsiri Oku",
        "bookmark_btn": "🔖 Yer İmi",
        "more_hadith": "🔄 Başka hadis",
        "translate_btn": "🌐 Çevir",
        "surah_word": "Sure",
        "ayah_word": "Ayet",
        "full_tafsir_hint": "👇 Tam tefsir için aşağıdaki düğmeye basın",
        "blessing": "🤲 Allah sizi ilimle mübarek kılsın.",
        "loading": "📖 Ayet yükleniyor… ✨",
        "load_error": "❌ Yükleme hatası. Tekrar deneyin.",
        "welcome": (
            "✨ <b>Es-selamu aleyküm!</b> ✨\n\n"
            "<b>Kur'an ve Tefsir Bot</b>'a hoş geldiniz! 🕌\n\n"
            "📅 <b>Özellikler:</b>\n"
            "  • Günlük ayet + tefsir + hadis\n"
            "  • 📖 Tam tefsir için Mini App\n"
            "  • ⏰ Kişisel hatırlatmalar\n"
            "  • 🇷🇺 🇬🇧 🇹🇷 Çeviri (Google)\n"
            "  • ⬅️ ➡️ Ayet navigasyonu\n"
            "  • 🔍 Arama · 🔖 Yer İmleri\n\n"
            "🎮 <b>Komutlar:</b>\n"
            "/now — Şimdi rastgele ayet\n"
            "/ayah 2:255 — Belirli bir ayet\n"
            "/hadith — Rastgele hadis\n"
            "/remind 08:30 — Hatırlatma ekle\n"
            "/reminders — Hatırlatmalarım\n"
            "/search kelime — Tefsirde ara\n"
            "/bookmark 2:255 — Yer imi\n"
            "/bookmarks — Yer imlerim\n\n"
            "🤲 <i>Bu bot sizi Allah'ın sözlerine yaklaştırsın.</i>"
        ),
        "streak_days": "g",
        "streak_label": "Seri",
        "qurtubi_excerpt": "Kurtubi Tefsiri (alıntı)",
        "qushairi_excerpt": "Kuşeyri Tefsiri (alıntı)",
        "full_text_hint": "👇 Tam metin — aşağıdaki düğme",
        "ayah_usage": "📌 <b>Kullanım:</b> <code>/ayah 2:255</code>",
        "ayah_bad_format": "❌ Geçersiz format. <code>/ayah 2:255</code>",
        "hadith_title": "📿 <b>Hadis</b>",
        "search_hint": "🔍 <code>/search kelime</code> — tefsirde ara",
        "searching": "🔍 «{kw}» aranıyor…",
        "search_empty": "😔 «{kw}» için sonuç bulunamadı.",
        "search_results": "🔍 <b>Sonuçlar: «{kw}»</b> ({n})",
        "bookmark_usage": "🔖 <code>/bookmark 2:255</code>",
        "bookmark_bad": "❌ Format: <code>/bookmark 2:255</code>",
        "bookmark_added": "✅ <b>Yer imi:</b> {name} — {ref}",
        "bookmark_dup": "📌 Zaten yer imlerinde!",
        "bookmarks_empty": "📌 Yer imi yok. <code>/bookmark 2:255</code>",
        "bookmarks_title": "🔖 <b>Yer imleriniz:</b>",
        "remind_help": (
            "⏰ <b>Kullanım:</b>\n\n"
            "<code>/remind 08:30</code> — rastgele ayet\n"
            "<code>/remind 08:30 2:255</code> — belirli ayet\n"
            "<code>/remind 08:30 Sabah</code> — etiketli\n\n"
            "Sil: /reminders → /delremind numara"
        ),
        "remind_bad_time": "❌ Format: <code>HH:MM</code>",
        "remind_dup": "⚠️ {t} için zaten hatırlatma var.",
        "remind_ok": "✅ <b>Hatırlatma:</b> {t}  •  {desc}\n/reminders",
        "random_ayah": "rastgele ayet",
        "reminders_empty": "⏰ Hatırlatma yok. <code>/remind 08:30</code>",
        "reminders_title": "⏰ <b>Hatırlatmalarınız:</b>",
        "delremind_help": "<code>/delremind 1</code> veya <code>/delremind all</code>",
        "deleted_n": "🗑️ Silindi: {n}.",
        "deleted_ok": "✅ #{i} silindi.",
        "deleted_bad": "❌ #{i} yok. /reminders",
        "reminder_msg": "⏰ <b>Hatırlatma</b>",
        "msg_truncated": "\n\n⚠️ <i>Mesaj kısaltıldı.</i>",
        "reflections": [
            "💭 Her ayet tam bu an size gönderilen bir mesajdır.",
            "💭 Kur'an ruhun aynasıdır. Bugün ne görüyorsunuz?",
            "💭 Gerçek bilgi tefekkür ile gelir.",
            "💭 Allah'ın her sözü yolunuzu aydınlatsın.",
            "💭 Sabır ve şükür — müminin iki kanadı.",
            "💭 Her gün Allah'a yaklaşmak için bir fırsattır.",
            "💭 Kur'an'ın hikmeti kalbiyle arayanlara açılır.",
            "💭 Tefekkürün sessizliğinde anlayış doğar.",
            "💭 Allah hiçbir nefse taşıyamayacağı yükü yüklemez.",
            "💭 Bugünkü ayet tüm gününüze rehber olsun.",
        ],
    },
}


def S(lang: str) -> dict:
    """Get the i18n string dict for a language."""
    return _STRINGS.get(lang, _STRINGS["ru"])


# ═══════════════════════════════════════════
# 🌐  TRANSLATION  (deep-translator + cache)
# ═══════════════════════════════════════════

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_CACHE_FILE = os.path.join(_BASE_DIR, "translation_cache.json")
_cache: dict = {}
_cache_lock = threading.Lock()
_LANG_MAP = {"ru": "ru", "en": "en", "tr": "tr", "ar": "ar"}


def _load_cache():
    global _cache
    if os.path.exists(_CACHE_FILE):
        try:
            with open(_CACHE_FILE, "r", encoding="utf-8") as f:
                _cache = json.load(f)
            logger.info("📦 Translation cache: %d entries", len(_cache))
        except Exception:
            _cache = {}


def _save_cache():
    with _cache_lock:
        try:
            with open(_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(_cache, f, ensure_ascii=False)
        except Exception as e:
            logger.error("Cache save error: %s", e)


def _cache_key(text: str, src: str, tgt: str) -> str:
    h = hashlib.md5(f"{src}|{tgt}|{text}".encode("utf-8")).hexdigest()[:16]
    return h


def translate_text(text: str, target_lang: str, source_lang: str = "auto") -> str:
    """Translate text with paragraph chunking, caching, and safe fallback."""
    if not text or not text.strip():
        return text
    tgt = _LANG_MAP.get(target_lang, target_lang)
    src = _LANG_MAP.get(source_lang, source_lang)
    if tgt == src and src != "auto":
        return text

    ck = _cache_key(text, src, tgt)
    with _cache_lock:
        if ck in _cache:
            return _cache[ck]

    MAX_CHUNK = 4500
    paragraphs = text.split("\n")
    chunks: list[str] = []
    buf = ""
    for p in paragraphs:
        if len(buf) + len(p) + 1 > MAX_CHUNK and buf:
            chunks.append(buf)
            buf = p
        else:
            buf = (buf + "\n" + p) if buf else p
    if buf:
        chunks.append(buf)

    final: list[str] = []
    for c in chunks:
        while len(c) > MAX_CHUNK:
            final.append(c[:MAX_CHUNK])
            c = c[MAX_CHUNK:]
        final.append(c)

    translated_parts: list[str] = []
    try:
        translator = GoogleTranslator(source=src, target=tgt)
        for part in final:
            part = part.strip()
            if not part:
                translated_parts.append("")
                continue
            pck = _cache_key(part, src, tgt)
            with _cache_lock:
                if pck in _cache:
                    translated_parts.append(_cache[pck])
                    continue
            result = translator.translate(part)
            if result:
                translated_parts.append(result)
                with _cache_lock:
                    _cache[pck] = result
            else:
                translated_parts.append(part)
            _time.sleep(0.15)
    except Exception as e:
        logger.warning("Translation %s→%s failed: %s — returning original", src, tgt, e)
        return text

    full_result = "\n".join(translated_parts)
    with _cache_lock:
        _cache[ck] = full_result
    if len(_cache) % 20 == 0:
        _save_cache()
    return full_result


# ═══════════════════════════════════════════
# 📡  QURAN  &  HADITH  APIs
# ═══════════════════════════════════════════

def fetch_ayah_text(surah: int, ayah: int, lang: str = "ru") -> dict | None:
    try:
        edition = QURAN_EDITIONS.get(lang, DEFAULT_TRANSLATION)
        r = requests.get(
            f"{QURAN_API_BASE}/ayah/{surah}:{ayah}/editions/quran-unicode,{edition}",
            timeout=10,
        ).json()
        if r.get("code") == 200:
            return {
                "arabic": r["data"][0]["text"],
                "translation": r["data"][1]["text"],
                "surah_en": r["data"][0]["surah"]["englishName"],
                "surah_ar": r["data"][0]["surah"]["name"],
                "surah_num": surah,
                "ayah": ayah,
            }
    except Exception as e:
        logger.error("Quran API error: %s", e)
    return None


def fetch_random_ayah(lang: str = "ru") -> dict | None:
    try:
        s = random.randint(1, 114)
        total = get_ayah_count(s)
        a = random.randint(1, total) if total > 0 else 1
        return fetch_ayah_text(s, a, lang)
    except Exception as e:
        logger.error("Random ayah error: %s", e)
        return None


def fetch_random_hadith() -> dict:
    """Fetch a random hadith from Sahih Bukhari via fawazahmed0 CDN."""
    try:
        section = random.randint(1, HADITH_SECTIONS)
        url = f"{HADITH_API_BASE}/{section}.json"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        hadiths = data.get("hadiths", [])
        if hadiths:
            h = random.choice(hadiths)
            text = h.get("text", "")
            num = h.get("hadithnumber", "?")
            ref_data = h.get("reference", {})
            book = ref_data.get("book", section) if isinstance(ref_data, dict) else section
            return {
                "text": text,
                "reference": f"Sahih al-Bukhari — Book {book}, Hadith {num}",
            }
    except Exception as e:
        logger.error("Hadith API error: %s", e)
    return {
        "text": "Actions are judged by intentions, so each man will have what he intended.",
        "reference": "Sahih al-Bukhari, Hadith 1",
    }


def _translate_hadith(text: str, lang: str) -> str:
    if lang == "en" or not text:
        return text
    try:
        return translate_text(text, lang, "en")
    except Exception:
        return text


# ═══════════════════════════════════════════
# 🎨  MESSAGE  FORMATTING  (fully localised)
# ═══════════════════════════════════════════

def _streak_emoji(streak: int, lang: str) -> str:
    if streak <= 0:
        return ""
    s = S(lang)
    return "🔥" * min(streak, 7) + f" {s['streak_label']}: {streak} {s['streak_days']}"


def _webapp_url(surah: int, ayah: int, lang: str) -> str:
    return f"{WEBAPP_URL}/webapp?surah={surah}&ayah={ayah}&lang={lang}"


def _build_ayah_keyboard(surah: int, ayah: int, lang: str) -> InlineKeyboardMarkup:
    ps, pa = get_prev_ayah(surah, ayah)
    ns, na = get_next_ayah(surah, ayah)
    s = S(lang)
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⬅️", callback_data=f"nav_{ps}_{pa}_{lang}"),
            InlineKeyboardButton(f"📍 {surah}:{ayah}", callback_data="noop"),
            InlineKeyboardButton("➡️", callback_data=f"nav_{ns}_{na}_{lang}"),
        ],
        [
            InlineKeyboardButton(
                s["tafsir_btn"],
                web_app=WebAppInfo(url=_webapp_url(surah, ayah, lang)),
            ),
        ],
        [
            InlineKeyboardButton(label, callback_data=f"lang_{code}_{surah}_{ayah}")
            for code, label in AVAILABLE_TRANSLATIONS.items()
            if code != lang
        ],
        [InlineKeyboardButton(s["bookmark_btn"], callback_data=f"bmark_{surah}_{ayah}")],
    ])


def _build_hadith_keyboard(lang: str) -> InlineKeyboardMarkup:
    s = S(lang)
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(s["more_hadith"], callback_data="another_hadith"),
        InlineKeyboardButton(s["translate_btn"], callback_data="translate_hadith"),
    ]])


def format_ayah_compact(ayah_data: dict, hadith: dict | None,
                        lang: str, streak: int = 0) -> str:
    s = S(lang)
    s_ar = get_surah_name(ayah_data["surah_num"])
    s_en = ayah_data.get("surah_en", "")
    su, ay = ayah_data["surah_num"], ayah_data["ayah"]
    flag = {"ru": "🇷🇺", "en": "🇬🇧", "tr": "🇹🇷"}.get(lang, "🌍")
    streak_line = f"\n{_streak_emoji(streak, lang)}" if streak > 0 else ""

    msg = (
        f"╔══════════════════════════╗\n"
        f"   ✨ <b>{s['title']}</b> ✨\n"
        f"╚══════════════════════════╝{streak_line}\n\n"
        f"🕌 <b>{s_ar} ({s_en})</b>\n"
        f"📍 {s['surah_word']} {su}, {s['ayah_word']} {ay}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📜 <b>{s['arabic_label']}:</b>\n"
        f"<i>{ayah_data['arabic']}</i>\n\n"
        f"{flag} <b>{s['translation_label']}:</b>\n"
        f"{ayah_data['translation']}\n"
    )

    if hadith:
        h = _translate_hadith(hadith["text"], lang)
        if len(h) > 300:
            h = h[:297] + "…"
        msg += (
            f"\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📿 <b>{s['hadith_label']}:</b>\n<i>{h}</i>\n"
            f"📖 <i>{hadith['reference']}</i>"
        )

    msg += (
        f"\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{random.choice(s['reflections'])}\n\n"
        f"{s['full_tafsir_hint']}\n"
        f"{s['blessing']}"
    )
    return msg


def format_ayah_full(ayah_data: dict, qurtubi: str, qushairi: str,
                     hadith: dict | None, lang: str, streak: int = 0) -> str:
    s = S(lang)
    s_ar = get_surah_name(ayah_data["surah_num"])
    s_en = ayah_data.get("surah_en", "")
    su, ay = ayah_data["surah_num"], ayah_data["ayah"]
    flag = {"ru": "🇷🇺", "en": "🇬🇧", "tr": "🇹🇷"}.get(lang, "🌍")

    q = translate_text(qurtubi, lang, "ar") if lang != "ar" else qurtubi
    qs = translate_text(qushairi, lang, "en") if lang != "en" else qushairi

    streak_line = f"\n{_streak_emoji(streak, lang)}" if streak > 0 else ""

    msg = (
        f"╔══════════════════════════╗\n"
        f"   ✨ <b>{s['title']}</b> ✨\n"
        f"╚══════════════════════════╝{streak_line}\n\n"
        f"🕌 <b>{s_ar} ({s_en})</b>\n"
        f"📍 {s['surah_word']} {su}, {s['ayah_word']} {ay}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📜 <b>{s['arabic_label']}:</b>\n<i>{ayah_data['arabic']}</i>\n\n"
        f"{flag} <b>{s['translation_label']}:</b>\n{ayah_data['translation']}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📚 <b>{s['qurtubi_excerpt']}:</b>\n{q}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📖 <b>{s['qushairi_excerpt']}:</b>\n{qs}\n\n"
        f"{s['full_text_hint']}\n"
        f"{s['blessing']}"
    )
    return msg


# ── safe send / edit ─────────────────────────────────────────────

async def _safe_send(target, text: str, *, chat_id=None,
                     keyboard=None, parse_mode="HTML", lang="ru"):
    """Send or edit a Telegram message, truncating if needed."""
    txt = text[:4096]
    try:
        if chat_id:
            return await target.send_message(
                chat_id=chat_id, text=txt,
                parse_mode=parse_mode, reply_markup=keyboard)
        # CallbackQuery — use .edit_message_text
        if hasattr(target, "edit_message_text"):
            return await target.edit_message_text(
                txt, parse_mode=parse_mode, reply_markup=keyboard)
        # Message object — use .edit_text
        if hasattr(target, "edit_text"):
            return await target.edit_text(
                txt, parse_mode=parse_mode, reply_markup=keyboard)
    except Exception as e:
        logger.warning("Message send/edit error: %s", e)
        s = S(lang)
        short = text[:3900] + s["msg_truncated"]
        try:
            if chat_id:
                return await target.send_message(
                    chat_id=chat_id, text=short,
                    parse_mode=parse_mode, reply_markup=keyboard)
            if hasattr(target, "edit_message_text"):
                return await target.edit_message_text(
                    short, parse_mode=parse_mode, reply_markup=keyboard)
            if hasattr(target, "edit_text"):
                return await target.edit_text(
                    short, parse_mode=parse_mode, reply_markup=keyboard)
        except Exception:
            pass


# ═══════════════════════════════════════════
# 🤖  BOT COMMANDS
# ═══════════════════════════════════════════

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = user_data.get_language(uid)
    s = S(lang)
    await update.message.reply_text(s["welcome"], parse_mode="HTML")


async def cmd_now(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = user_data.get_language(uid)
    s = S(lang)
    streak = user_data.get_streak(uid)["current"]

    wait = await update.message.reply_text(s["loading"])
    data = fetch_random_ayah(lang)
    if not data:
        await wait.edit_text(s["load_error"])
        return

    su, ay = data["surah_num"], data["ayah"]
    hadith = fetch_random_hadith()
    user_data.mark_ayah_read(uid, su, ay)

    msg = format_ayah_compact(data, hadith, lang, streak)
    kb = _build_ayah_keyboard(su, ay, lang)
    await _safe_send(wait, msg, keyboard=kb, lang=lang)


async def cmd_ayah(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = user_data.get_language(uid)
    s = S(lang)
    streak = user_data.get_streak(uid)["current"]

    if not ctx.args:
        await update.message.reply_text(s["ayah_usage"], parse_mode="HTML")
        return
    try:
        parts = ctx.args[0].split(":")
        su, ay = int(parts[0]), int(parts[1])
        assert 1 <= su <= 114 and 1 <= ay <= get_ayah_count(su)
    except Exception:
        await update.message.reply_text(s["ayah_bad_format"], parse_mode="HTML")
        return

    wait = await update.message.reply_text(s["loading"])
    data = fetch_ayah_text(su, ay, lang)
    if not data:
        await wait.edit_text(s["load_error"])
        return

    q = get_tafsir_for_ayah(su, ay, "qurtubi")
    qs = get_tafsir_for_ayah(su, ay, "qushairi")
    user_data.mark_ayah_read(uid, su, ay)

    msg = format_ayah_full(data, q, qs, None, lang, streak)
    kb = _build_ayah_keyboard(su, ay, lang)
    await _safe_send(wait, msg, keyboard=kb, lang=lang)


async def cmd_hadith(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = user_data.get_language(uid)
    s = S(lang)
    h = fetch_random_hadith()
    txt = _translate_hadith(h["text"], lang)
    msg = f"{s['hadith_title']}\n\n<i>{txt}</i>\n\n📖 <i>{h['reference']}</i>"
    await update.message.reply_text(
        msg, parse_mode="HTML", reply_markup=_build_hadith_keyboard(lang))


async def cmd_search(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = user_data.get_language(uid)
    s = S(lang)
    if not ctx.args:
        await update.message.reply_text(s["search_hint"], parse_mode="HTML")
        return
    kw = " ".join(ctx.args)
    await update.message.reply_text(s["searching"].format(kw=kw))
    results = search_tafsir(kw, "qushairi", max_results=8)
    if not results:
        await update.message.reply_text(s["search_empty"].format(kw=kw))
        return
    msg = s["search_results"].format(kw=kw, n=len(results)) + "\n\n"
    for i, r in enumerate(results, 1):
        snip = r["snippet"].replace("<", "&lt;").replace(">", "&gt;")
        msg += f"<b>{i}. {r['surah_name']} — {r['surah']}:{r['ayah']}</b>\n<i>{snip}</i>\n\n"
    msg += "📌 <code>/ayah surah:ayah</code>"
    try:
        await update.message.reply_text(msg, parse_mode="HTML")
    except Exception:
        await update.message.reply_text(msg[:4000], parse_mode="HTML")


async def cmd_bookmark(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = user_data.get_language(uid)
    s = S(lang)
    if not ctx.args:
        await update.message.reply_text(s["bookmark_usage"], parse_mode="HTML")
        return
    try:
        parts = ctx.args[0].split(":")
        su, ay = int(parts[0]), int(parts[1])
    except Exception:
        await update.message.reply_text(s["bookmark_bad"], parse_mode="HTML")
        return
    if user_data.add_bookmark(uid, su, ay):
        await update.message.reply_text(
            s["bookmark_added"].format(name=get_surah_name(su), ref=f"{su}:{ay}"),
            parse_mode="HTML")
    else:
        await update.message.reply_text(s["bookmark_dup"])


async def cmd_bookmarks(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = user_data.get_language(uid)
    s = S(lang)
    bm = user_data.get_bookmarks(uid)
    if not bm:
        await update.message.reply_text(s["bookmarks_empty"], parse_mode="HTML")
        return
    msg = s["bookmarks_title"] + "\n\n"
    for i, ref in enumerate(bm, 1):
        su = int(ref.split(":")[0])
        msg += f"  {i}. {get_surah_name(su)} — <code>{ref}</code>\n"
    msg += f"\n📌 <code>/ayah surah:ayah</code>"
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_progress(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    stats = user_data.get_reading_stats(uid)
    sk = user_data.get_streak(uid)
    bar = user_data.get_progress_bar(stats["percentage"])
    msg = (
        f"📊 <b>Progress</b>\n\n{bar}\n\n"
        f"📖 {stats['total_read']} / {stats['total_ayahs']}  ({stats['percentage']}%)\n\n"
        f"🔥 {sk['current']} (max {sk['max']})"
    )
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_times(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lines = "\n".join(f"  🕐 {t}" for t in SCHEDULE_TIMES)
    msg = f"⏰ <b>Schedule ({len(SCHEDULE_TIMES)}/day)</b>\n\n{lines}"
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_lang(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    cur = user_data.get_language(uid)
    kb = [[InlineKeyboardButton(
        f"{lb}{' ✅' if c == cur else ''}", callback_data=f"setlang_{c}")]
        for c, lb in AVAILABLE_TRANSLATIONS.items()]
    await update.message.reply_text(
        f"🌍 <b>{AVAILABLE_TRANSLATIONS.get(cur, cur)}</b>",
        parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))


# ═══════════════════════════════════════════
# ⏰  REMINDER COMMANDS (localised)
# ═══════════════════════════════════════════

async def cmd_remind(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = user_data.get_language(uid)
    s = S(lang)
    if not ctx.args:
        await update.message.reply_text(s["remind_help"], parse_mode="HTML")
        return
    time_str = ctx.args[0]
    try:
        hh, mm = time_str.split(":")
        assert 0 <= int(hh) <= 23 and 0 <= int(mm) <= 59
        time_str = f"{int(hh):02d}:{int(mm):02d}"
    except Exception:
        await update.message.reply_text(s["remind_bad_time"], parse_mode="HTML")
        return

    surah, ayah, label = None, None, ""
    if len(ctx.args) > 1:
        rest = " ".join(ctx.args[1:])
        if ":" in rest.split()[0]:
            try:
                p = rest.split()[0].split(":")
                surah, ayah = int(p[0]), int(p[1])
                assert 1 <= surah <= 114 and 1 <= ayah <= get_ayah_count(surah)
                label = " ".join(rest.split()[1:])
            except Exception:
                surah, ayah = None, None
                label = rest
        else:
            label = rest

    result = user_data.add_reminder(uid, time_str, surah, ayah, label)
    if result is None:
        await update.message.reply_text(s["remind_dup"].format(t=time_str))
        return
    desc = f"{surah}:{ayah}" if surah else s["random_ayah"]
    if label:
        desc += f" — {label}"
    await update.message.reply_text(
        s["remind_ok"].format(t=time_str, desc=desc), parse_mode="HTML")
    _register_reminder_job(uid, result, ctx.application)


async def cmd_reminders(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = user_data.get_language(uid)
    s = S(lang)
    rems = user_data.get_reminders(uid)
    if not rems:
        await update.message.reply_text(s["reminders_empty"], parse_mode="HTML")
        return
    msg = s["reminders_title"] + "\n\n"
    for i, r in enumerate(rems, 1):
        status = "✅" if r.get("active", True) else "⏸️"
        ai = f" — {r['surah']}:{r['ayah']}" if r.get("surah") else f" — {s['random_ayah']}"
        li = f"  «{r['label']}»" if r.get("label") else ""
        msg += f"  {status} {i}. <b>{r['time']}</b>{ai}{li}\n"
    msg += f"\n<code>/delremind 1</code>"
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_delremind(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = user_data.get_language(uid)
    s = S(lang)
    if not ctx.args:
        await update.message.reply_text(s["delremind_help"], parse_mode="HTML")
        return
    if ctx.args[0].lower() == "all":
        count = user_data.clear_reminders(uid)
        _remove_all_reminder_jobs(uid)
        await update.message.reply_text(s["deleted_n"].format(n=count))
        return
    try:
        idx = int(ctx.args[0])
    except ValueError:
        await update.message.reply_text(s["delremind_help"], parse_mode="HTML")
        return
    rems = user_data.get_reminders(uid)
    if 1 <= idx <= len(rems):
        _remove_reminder_job(uid, rems[idx - 1]["time"])
    if user_data.remove_reminder(uid, idx):
        await update.message.reply_text(s["deleted_ok"].format(i=idx))
    else:
        await update.message.reply_text(s["deleted_bad"].format(i=idx))


# ═══════════════════════════════════════════
# 🔄  CALLBACK HANDLERS
# ═══════════════════════════════════════════

async def handle_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    d = query.data
    if d == "noop":
        await query.answer()
        return
    if d.startswith("nav_"):
        await _cb_nav(query)
    elif d.startswith("lang_"):
        await _cb_lang(query)
    elif d.startswith("setlang_"):
        await _cb_setlang(query)
    elif d.startswith("bmark_"):
        await _cb_bookmark(query)
    elif d == "another_hadith":
        await _cb_hadith(query)
    elif d == "translate_hadith":
        await _cb_translate_hadith(query)
    else:
        await query.answer("❓")


async def _cb_nav(query):
    await query.answer()
    try:
        p = query.data.split("_")
        su, ay, lang = int(p[1]), int(p[2]), p[3] if len(p) > 3 else "ru"
    except Exception:
        return
    uid = query.from_user.id
    streak = user_data.get_streak(uid)["current"]
    data = fetch_ayah_text(su, ay, lang)
    if not data:
        await query.answer("❌")
        return
    user_data.mark_ayah_read(uid, su, ay)
    msg = format_ayah_compact(data, None, lang, streak)
    kb = _build_ayah_keyboard(su, ay, lang)
    await _safe_send(query, msg, keyboard=kb, lang=lang)


async def _cb_lang(query):
    """Language button on an ayah message — switch lang, save preference, re-render."""
    await query.answer()
    try:
        p = query.data.split("_")
        lang, su, ay = p[1], int(p[2]), int(p[3])
    except Exception:
        return
    uid = query.from_user.id
    # Save the new language preference
    user_data.set_language(uid, lang)
    streak = user_data.get_streak(uid)["current"]
    data = fetch_ayah_text(su, ay, lang)
    if not data:
        await query.answer("❌")
        return
    msg = format_ayah_compact(data, None, lang, streak)
    kb = _build_ayah_keyboard(su, ay, lang)
    await _safe_send(query, msg, keyboard=kb, lang=lang)


async def _cb_setlang(query):
    lang = query.data.replace("setlang_", "")
    uid = query.from_user.id
    user_data.set_language(uid, lang)
    lb = AVAILABLE_TRANSLATIONS.get(lang, lang)
    await query.answer(f"✅ {lb}")
    kb = [[InlineKeyboardButton(
        f"{l}{' ✅' if c == lang else ''}", callback_data=f"setlang_{c}")]
        for c, l in AVAILABLE_TRANSLATIONS.items()]
    await query.edit_message_text(
        f"🌍 <b>{lb}</b>", parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(kb))


async def _cb_bookmark(query):
    try:
        p = query.data.split("_")
        su, ay = int(p[1]), int(p[2])
    except Exception:
        await query.answer("❌")
        return
    uid = query.from_user.id
    if user_data.add_bookmark(uid, su, ay):
        await query.answer(f"✅ {get_surah_name(su)} {su}:{ay}")
    else:
        lang = user_data.get_language(uid)
        await query.answer(S(lang)["bookmark_dup"])


async def _cb_hadith(query):
    await query.answer()
    uid = query.from_user.id
    lang = user_data.get_language(uid)
    s = S(lang)
    h = fetch_random_hadith()
    txt = _translate_hadith(h["text"], lang)
    msg = f"{s['hadith_title']}\n\n<i>{txt}</i>\n\n📖 <i>{h['reference']}</i>"
    await _safe_send(query, msg, keyboard=_build_hadith_keyboard(lang), lang=lang)


async def _cb_translate_hadith(query):
    await query.answer()
    orig = query.message.text or ""
    if not orig:
        return
    en = translate_text(orig, "en", "auto")
    tr = translate_text(orig, "tr", "auto")
    msg = f"🇬🇧 <b>English:</b>\n{en}\n\n🇹🇷 <b>Türkçe:</b>\n{tr}"
    try:
        await query.message.reply_text(msg, parse_mode="HTML")
    except Exception:
        await query.message.reply_text(msg[:4000], parse_mode="HTML")


# ═══════════════════════════════════════════
# ⏰  SCHEDULED  +  REMINDER  ENGINE
# ═══════════════════════════════════════════

_scheduler: AsyncIOScheduler | None = None
_bot_app: Application | None = None


async def send_scheduled_message(app: Application):
    try:
        lang = user_data.get_language(CHAT_ID)
        data = fetch_random_ayah(lang)
        if not data:
            logger.error("Scheduled: fetch failed")
            return
        su, ay = data["surah_num"], data["ayah"]
        hadith = fetch_random_hadith()
        msg = format_ayah_compact(data, hadith, lang, 0)
        kb = _build_ayah_keyboard(su, ay, lang)
        await app.bot.send_message(
            chat_id=CHAT_ID, text=msg[:4096],
            parse_mode="HTML", reply_markup=kb)
        logger.info("✅ Scheduled → %s:%s", su, ay)
    except Exception as e:
        logger.error("Scheduled error: %s", e)


async def send_reminder_message(app: Application, uid: int,
                                surah: int | None, ayah: int | None,
                                label: str):
    try:
        lang = user_data.get_language(uid)
        s = S(lang)
        data = fetch_ayah_text(surah, ayah, lang) if surah and ayah else fetch_random_ayah(lang)
        if not data:
            return
        su, ay = data["surah_num"], data["ayah"]
        user_data.mark_ayah_read(uid, su, ay)
        label_line = f"\n📝 <i>{label}</i>" if label else ""
        s_ar = get_surah_name(su)
        s_en = data.get("surah_en", "")
        flag = {"ru": "🇷🇺", "en": "🇬🇧", "tr": "🇹🇷"}.get(lang, "🌍")
        msg = (
            f"{s['reminder_msg']}{label_line}\n\n"
            f"🕌 <b>{s_ar} ({s_en})</b>  •  {su}:{ay}\n\n"
            f"📜 <i>{data['arabic']}</i>\n\n"
            f"{flag} {data['translation']}\n\n"
            f"{random.choice(s['reflections'])}\n\n"
            f"{s['full_tafsir_hint']}"
        )
        kb = _build_ayah_keyboard(su, ay, lang)
        await app.bot.send_message(chat_id=uid, text=msg[:4096],
                                   parse_mode="HTML", reply_markup=kb)
        logger.info("⏰ Reminder → uid=%s  %s:%s", uid, su, ay)
    except Exception as e:
        logger.error("Reminder error uid=%s: %s", uid, e)


def _reminder_job_id(uid, time_str: str) -> str:
    return f"remind_{uid}_{time_str}"


def _register_reminder_job(uid, reminder: dict, app: Application):
    if not _scheduler:
        return
    jid = _reminder_job_id(uid, reminder["time"])
    hh, mm = map(int, reminder["time"].split(":"))
    try:
        _scheduler.remove_job(jid)
    except Exception:
        pass
    _scheduler.add_job(
        send_reminder_message, "cron", hour=hh, minute=mm,
        args=[app, int(uid), reminder.get("surah"), reminder.get("ayah"),
              reminder.get("label", "")],
        id=jid)


def _remove_reminder_job(uid, time_str: str):
    if not _scheduler:
        return
    try:
        _scheduler.remove_job(_reminder_job_id(uid, time_str))
    except Exception:
        pass


def _remove_all_reminder_jobs(uid):
    if not _scheduler:
        return
    for r in user_data.get_reminders(uid):
        _remove_reminder_job(uid, r["time"])


def _load_all_reminders(app: Application):
    all_rems = user_data.get_all_reminders()
    count = 0
    for uid_str, rems in all_rems.items():
        for r in rems:
            if r.get("active", True):
                _register_reminder_job(uid_str, r, app)
                count += 1
    logger.info("📅 Loaded %d reminders", count)


# ═══════════════════════════════════════════
# 🌐  FLASK WEB SERVER
# ═══════════════════════════════════════════

flask_app = Flask(__name__, static_folder="webapp", static_url_path="/static")
CORS(flask_app)


@flask_app.after_request
def _add_ngrok_headers(response):
    """Allow ngrok interstitial bypass for Telegram's embedded browser."""
    response.headers["ngrok-skip-browser-warning"] = "true"
    return response


@flask_app.route("/")
def serve_root():
    """Root URL redirect — so ngrok URL opens the webapp directly."""
    return send_from_directory("webapp", "index.html")


@flask_app.route("/webapp")
def serve_webapp():
    return send_from_directory("webapp", "index.html")


@flask_app.route("/webapp/<path:filename>")
def serve_webapp_file(filename):
    return send_from_directory("webapp", filename)


@flask_app.route("/api/tafsir")
def api_tafsir():
    """
    GET /api/tafsir?surah=1&ayah=1&lang=ru
    Returns TRANSLATED tafsir based on lang parameter.
    """
    try:
        surah = int(flask_request.args.get("surah", 1))
        ayah = int(flask_request.args.get("ayah", 1))
        lang = flask_request.args.get("lang", "ru")
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid params"}), 400
    if not (1 <= surah <= 114):
        return jsonify({"error": "Surah 1-114"}), 400
    mx = get_ayah_count(surah)
    if not (1 <= ayah <= mx):
        return jsonify({"error": f"Ayah 1-{mx}"}), 400

    raw_qurtubi = get_full_tafsir(surah, ayah, "qurtubi")
    raw_qushairi = get_full_tafsir(surah, ayah, "qushairi")

    if lang == "ar":
        t_qurtubi = raw_qurtubi
        t_qushairi = translate_text(raw_qushairi, "ar", "en")
    elif lang == "en":
        t_qurtubi = translate_text(raw_qurtubi, "en", "ar")
        t_qushairi = raw_qushairi
    elif lang == "tr":
        t_qurtubi = translate_text(raw_qurtubi, "tr", "ar")
        t_qushairi = translate_text(raw_qushairi, "tr", "en")
    else:
        t_qurtubi = translate_text(raw_qurtubi, "ru", "ar")
        t_qushairi = translate_text(raw_qushairi, "ru", "en")

    ps, pa = get_prev_ayah(surah, ayah)
    ns, na = get_next_ayah(surah, ayah)

    return jsonify({
        "surah_num": surah, "ayah_num": ayah,
        "surah_name": get_surah_name(surah),
        "qurtubi": t_qurtubi,
        "qushairi": t_qushairi,
        "qurtubi_raw": raw_qurtubi,
        "qushairi_raw": raw_qushairi,
        "qurtubi_length": len(t_qurtubi),
        "qushairi_length": len(t_qushairi),
        "lang": lang,
        "translated": lang not in ("ar",),
        "nav": {"prev": {"surah": ps, "ayah": pa},
                "next": {"surah": ns, "ayah": na}},
    })


@flask_app.route("/api/surah-list")
def api_surah_list():
    return jsonify({"surahs": [
        {"num": n, "name": SURAH_NAMES.get(n, ""),
         "ayah_count": SURAH_AYAH_COUNT.get(n, 0)}
        for n in range(1, 115)
    ]})


@flask_app.route("/api/health")
def api_health():
    return jsonify({"status": "ok", "cache_size": len(_cache)})


def _run_flask():
    flask_app.run(host=FLASK_HOST, port=FLASK_PORT,
                  debug=False, use_reloader=False)


# ═══════════════════════════════════════════
# 🚀  MAIN
# ═══════════════════════════════════════════

async def main():
    global _scheduler, _bot_app

    _load_cache()

    logger.info("🤖 Starting Quran & Tafsir Bot…")
    logger.info("🌐 Web App URL: %s", WEBAPP_URL)

    flask_thread = threading.Thread(target=_run_flask, daemon=True)
    flask_thread.start()
    logger.info("🌐 Flask → %s:%s", FLASK_HOST, FLASK_PORT)

    app = Application.builder().token(BOT_TOKEN).build()
    _bot_app = app

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("now", cmd_now))
    app.add_handler(CommandHandler("ayah", cmd_ayah))
    app.add_handler(CommandHandler("hadith", cmd_hadith))
    app.add_handler(CommandHandler("search", cmd_search))
    app.add_handler(CommandHandler("bookmark", cmd_bookmark))
    app.add_handler(CommandHandler("bookmarks", cmd_bookmarks))
    app.add_handler(CommandHandler("progress", cmd_progress))
    app.add_handler(CommandHandler("times", cmd_times))
    app.add_handler(CommandHandler("lang", cmd_lang))
    app.add_handler(CommandHandler("remind", cmd_remind))
    app.add_handler(CommandHandler("reminders", cmd_reminders))
    app.add_handler(CommandHandler("delremind", cmd_delremind))
    app.add_handler(CallbackQueryHandler(handle_callback))

    _scheduler = AsyncIOScheduler()
    for t in SCHEDULE_TIMES:
        hh, mm = map(int, t.split(":"))
        _scheduler.add_job(send_scheduled_message, "cron",
                           hour=hh, minute=mm, args=[app])
    _load_all_reminders(app)
    _scheduler.start()

    logger.info("📅 %d schedules + reminders loaded", len(SCHEDULE_TIMES))
    logger.info("✅ Bot running!  Ctrl+C to stop.")

    await app.initialize()
    await app.start()

    # ── Set the bot's command menu (the buttons users see) ──
    from telegram import BotCommand
    await app.bot.set_my_commands([
        BotCommand("now", "Random ayah / Случайный аят"),
        BotCommand("ayah", "Specific ayah / Конкретный аят"),
        BotCommand("hadith", "Random hadith / Хадис"),
        BotCommand("remind", "Add reminder / Напоминание"),
        BotCommand("reminders", "My reminders / Мои напоминания"),
        BotCommand("search", "Search tafsir / Поиск"),
        BotCommand("bookmark", "Bookmark ayah / Закладка"),
        BotCommand("bookmarks", "My bookmarks / Закладки"),
        BotCommand("lang", "Change language / Язык"),
        BotCommand("start", "Welcome / Начало"),
    ])
    logger.info("📋 Bot menu commands updated")

    await app.updater.start_polling()

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down…")
        _save_cache()
        _scheduler.shutdown()
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        _save_cache()
        logger.info("👋 Stopped.")
