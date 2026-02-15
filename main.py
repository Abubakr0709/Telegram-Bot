#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🕌 Коран и Тафсир — Telegram Bot
─────────────────────────────────
Минималистичный бот: /random · /hadith · /bookmarks
Перевод: Google Translate (deep-translator, бесплатно).
Весь интерфейс на русском. Аяты — на арабском + перевод.

Один процесс запускает:
  • Telegram-бот (polling)
  • Flask-сервер (Mini Web App для тафсира)
  • APScheduler (ежедневные аяты по расписанию)
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
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand,
    WebAppInfo,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import (
    BOT_TOKEN,
    CHAT_ID,
    SCHEDULE_TIMES,
    QURAN_API_BASE,
    HADITH_API_BASE,
    HADITH_SECTIONS,
    DEFAULT_TRANSLATION,
    WEBAPP_URL,
    FLASK_HOST,
    FLASK_PORT,
)
from tafsir_loader import (
    get_tafsir_for_ayah,
    get_full_tafsir,
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
# 🎨  СТРОКИ  ИНТЕРФЕЙСА  (только русский)
# ═══════════════════════════════════════════

_REFLECTIONS = [
    "💭 Каждый аят — послание именно для вас в этот момент.",
    "💭 Коран — зеркало души. Что вы видите сегодня?",
    "💭 Истинное знание приходит через размышление.",
    "💭 Пусть каждое слово Аллаха станет светом на вашем пути.",
    "💭 Терпение и благодарность — два крыла верующего.",
    "💭 Каждый день — возможность стать ближе к Аллаху.",
    "�� Мудрость Корана раскрывается тем, кто ищет сердцем.",
    "💭 В тишине размышления рождается понимание.",
    "💭 Аллах не обременяет душу сверх её возможностей.",
    "💭 Пусть сегодняшний аят станет проводником на весь день.",
]

_WELCOME = (
    "﷽\n\n"
    "✨ <b>Ас-саляму алейкум!</b>\n\n"
    "Я — <b>Коран и Тафсир</b>, ваш проводник\n"
    "к словам Всевышнего.\n\n"
    "┌─────────────────────┐\n"
    "│  /random  — случайный аят    │\n"
    "│  /hadith  — хадис дня            │\n"
    "│  /bookmarks — закладки        │\n"
    "└─────────────────────┘\n\n"
    "📖 К каждому аяту прилагается полный\n"
    "тафсир аль-Куртуби и аль-Кушайри\n"
    "в отдельном Mini App.\n\n"
    "🤲 <i>Пусть этот бот приблизит вас\n"
    "к словам Аллаха.</i>"
)


# ═══════════════════════════════════════════
# 🌐  ПЕРЕВОД  (Google Translate + кэш)
# ═══════════════════════════════════════════

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_CACHE_FILE = os.path.join(_BASE_DIR, "translation_cache.json")
_cache: dict = {}
_cache_lock = threading.Lock()


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


def translate_text(text: str, target_lang: str = "ru",
                   source_lang: str = "auto") -> str:
    """Translate with paragraph chunking, caching, and safe fallback."""
    if not text or not text.strip():
        return text
    if target_lang == source_lang and source_lang != "auto":
        return text

    ck = _cache_key(text, source_lang, target_lang)
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
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        for part in final:
            part = part.strip()
            if not part:
                translated_parts.append("")
                continue
            pck = _cache_key(part, source_lang, target_lang)
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
        logger.warning("Translation %s→%s failed: %s", source_lang, target_lang, e)
        return text

    full_result = "\n".join(translated_parts)
    with _cache_lock:
        _cache[ck] = full_result
    if len(_cache) % 20 == 0:
        _save_cache()
    return full_result


# ═══════════════════════════════════════════
# 📡  QURAN  &  HADITH  API
# ═══════════════════════════════════════════

def fetch_ayah(surah: int, ayah: int) -> dict | None:
    """Fetch Arabic text + Russian translation for a single ayah."""
    try:
        url = (f"{QURAN_API_BASE}/ayah/{surah}:{ayah}"
               f"/editions/quran-unicode,{DEFAULT_TRANSLATION}")
        r = requests.get(url, timeout=10).json()
        if r.get("code") == 200:
            ar_data = r["data"][0]
            return {
                "arabic": ar_data["text"],
                "translation": r["data"][1]["text"],
                "surah_en": ar_data["surah"]["englishName"],
                "surah_ar": ar_data["surah"]["name"],
                "surah_num": surah,
                "ayah_num": ayah,
                "total_ayahs": ar_data["surah"]["numberOfAyahs"],
            }
    except Exception as e:
        logger.error("Quran API error: %s", e)
    return None


def fetch_random_ayah() -> dict | None:
    """Fetch a random ayah from the entire Quran."""
    s = random.randint(1, 114)
    total = get_ayah_count(s)
    a = random.randint(1, total) if total > 0 else 1
    return fetch_ayah(s, a)


def fetch_random_hadith() -> dict:
    """Fetch a random hadith from Sahih Bukhari."""
    try:
        section = random.randint(1, HADITH_SECTIONS)
        url = f"{HADITH_API_BASE}/{section}.json"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        hadiths = data.get("hadiths", [])
        if hadiths:
            h = random.choice(hadiths)
            ref = h.get("reference", {})
            book = ref.get("book", section) if isinstance(ref, dict) else section
            return {
                "text": h.get("text", ""),
                "number": h.get("hadithnumber", "?"),
                "book": book,
            }
    except Exception as e:
        logger.error("Hadith API error: %s", e)
    return {
        "text": "Actions are judged by intentions, so each man will have what he intended.",
        "number": 1,
        "book": 1,
    }


# ═══════════════════════════════════════════
# 🎨  ФОРМАТИРОВАНИЕ  СООБЩЕНИЙ
# ═══════════════════════════════════════════

def _webapp_url(surah: int, ayah: int) -> str:
    return f"{WEBAPP_URL}/webapp?surah={surah}&ayah={ayah}&lang=ru"


def _ayah_keyboard(surah: int, ayah: int) -> InlineKeyboardMarkup:
    """Inline keyboard for an ayah message."""
    ps, pa = get_prev_ayah(surah, ayah)
    ns, na = get_next_ayah(surah, ayah)
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⬅️", callback_data=f"nav_{ps}_{pa}"),
            InlineKeyboardButton(f"📍 {surah}:{ayah}", callback_data="noop"),
            InlineKeyboardButton("➡️", callback_data=f"nav_{ns}_{na}"),
        ],
        [InlineKeyboardButton(
            "📖 Полный тафсир",
            web_app=WebAppInfo(url=_webapp_url(surah, ayah)),
        )],
        [InlineKeyboardButton("🔖 В закладки", callback_data=f"bm_{surah}_{ayah}")],
    ])


def _hadith_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard for a hadith message."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Ещё хадис", callback_data="more_hadith")],
    ])


def format_ayah_message(data: dict) -> str:
    """Format a full ayah message with tafsir excerpts."""
    su = data["surah_num"]
    ay = data["ayah_num"]
    s_ar = get_surah_name(su)
    s_en = data.get("surah_en", "")

    qurtubi = get_tafsir_for_ayah(su, ay, "qurtubi")
    qushairi = get_tafsir_for_ayah(su, ay, "qushairi")
    q_ru = translate_text(qurtubi, "ru", "ar")
    qs_ru = translate_text(qushairi, "ru", "en")

    if len(q_ru) > 600:
        q_ru = q_ru[:597] + "…"
    if len(qs_ru) > 400:
        qs_ru = qs_ru[:397] + "…"

    reflection = random.choice(_REFLECTIONS)

    return (
        f"┌───── ✦ КОРАН И ТАФСИР ✦ ─────┐\n\n"
        f"🕌  <b>{s_ar}</b>  ({s_en})\n"
        f"     Сура {su}, Аят {ay}\n\n"
        f"┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈\n\n"
        f"📜  <b>Арабский текст:</b>\n"
        f"<i>{data['arabic']}</i>\n\n"
        f"🇷🇺  <b>Перевод:</b>\n"
        f"{data['translation']}\n\n"
        f"┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈\n\n"
        f"📚  <b>Тафсир аль-Куртуби:</b>\n"
        f"<i>{q_ru}</i>\n\n"
        f"📖  <b>Тафсир аль-Кушайри:</b>\n"
        f"<i>{qs_ru}</i>\n\n"
        f"┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈\n\n"
        f"{reflection}\n\n"
        f"👇 Полный текст тафсира — кнопка ниже\n"
        f"🤲 Да благословит вас Аллах знанием."
    )


def format_hadith_message(h: dict) -> str:
    """Format a hadith message with Russian translation."""
    text_ru = translate_text(h["text"], "ru", "en") if h["text"] else ""
    if len(text_ru) > 1500:
        text_ru = text_ru[:1497] + "…"

    return (
        f"┌──── ✦ ХАДИС ДНЯ ✦ ────┐\n\n"
        f"📿  <i>{text_ru}</i>\n\n"
        f"┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈\n\n"
        f"📖  <i>Сахих аль-Бухари</i>\n"
        f"     Книга {h['book']}, Хадис {h['number']}\n\n"
        f"🤲 Да благословит вас Аллах знанием."
    )


def format_ayah_compact(data: dict, hadith: dict | None = None) -> str:
    """Compact format for scheduled messages and navigation."""
    su = data["surah_num"]
    ay = data["ayah_num"]
    s_ar = get_surah_name(su)
    s_en = data.get("surah_en", "")
    reflection = random.choice(_REFLECTIONS)

    msg = (
        f"┌───── ✦ КОРАН И ТАФСИР ✦ ─────┐\n\n"
        f"🕌  <b>{s_ar}</b>  ({s_en})\n"
        f"     Сура {su}, Аят {ay}\n\n"
        f"┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈\n\n"
        f"📜  <b>Арабский текст:</b>\n"
        f"<i>{data['arabic']}</i>\n\n"
        f"🇷🇺  <b>Перевод:</b>\n"
        f"{data['translation']}\n"
    )

    if hadith:
        h_ru = translate_text(hadith["text"], "ru", "en")
        if len(h_ru) > 300:
            h_ru = h_ru[:297] + "…"
        msg += (
            f"\n┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈\n\n"
            f"📿  <b>Хадис:</b>\n"
            f"<i>{h_ru}</i>\n"
            f"📖  <i>Сахих аль-Бухари — "
            f"Книга {hadith['book']}, Хадис {hadith['number']}</i>"
        )

    msg += (
        f"\n\n┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈\n\n"
        f"{reflection}\n\n"
        f"👇 Полный тафсир — кнопка ниже\n"
        f"🤲 Да благословит вас Аллах знанием."
    )
    return msg


# ── Безопасная отправка / редактирование ──

async def _safe_send(target, text: str, *, chat_id=None,
                     keyboard=None, parse_mode="HTML"):
    """Send or edit a Telegram message, truncating if needed."""
    txt = text[:4096]
    try:
        if chat_id:
            return await target.send_message(
                chat_id=chat_id, text=txt,
                parse_mode=parse_mode, reply_markup=keyboard)
        if hasattr(target, "edit_message_text"):
            return await target.edit_message_text(
                txt, parse_mode=parse_mode, reply_markup=keyboard)
        if hasattr(target, "edit_text"):
            return await target.edit_text(
                txt, parse_mode=parse_mode, reply_markup=keyboard)
    except Exception as e:
        logger.warning("Message send/edit error: %s", e)
        short = text[:3900] + "\n\n⚠️ <i>Сообщение сокращено.</i>"
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
# 🤖  ОБРАБОТЧИКИ  КОМАНД
# ═══════════════════════════════════════════

async def cmd_random(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """/random — случайный аят с тафсиром."""
    uid = update.effective_user.id

    # Auto-welcome for first-time users
    if not user_data.user_exists(uid):
        user_data.ensure_user(uid)
        await update.message.reply_text(_WELCOME, parse_mode="HTML")

    wait = await update.message.reply_text("📖 Загружаю аят… ✨")
    data = fetch_random_ayah()
    if not data:
        await wait.edit_text("❌ Ошибка загрузки. Попробуйте /random ещё раз.")
        return

    su, ay = data["surah_num"], data["ayah_num"]
    user_data.mark_ayah_read(uid, su, ay)
    msg = format_ayah_message(data)
    kb = _ayah_keyboard(su, ay)
    await _safe_send(wait, msg, keyboard=kb)


async def cmd_hadith(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """/hadith — случайный хадис."""
    uid = update.effective_user.id

    if not user_data.user_exists(uid):
        user_data.ensure_user(uid)
        await update.message.reply_text(_WELCOME, parse_mode="HTML")

    h = fetch_random_hadith()
    msg = format_hadith_message(h)
    await update.message.reply_text(
        msg, parse_mode="HTML", reply_markup=_hadith_keyboard())


async def cmd_bookmarks(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """/bookmarks — список сохранённых аятов."""
    uid = update.effective_user.id

    if not user_data.user_exists(uid):
        user_data.ensure_user(uid)

    bm = user_data.get_bookmarks(uid)
    if not bm:
        msg = (
            "🔖  <b>Закладки пусты</b>\n\n"
            "Нажмите  «🔖 В закладки»  под любым\n"
            "аятом, чтобы сохранить его.\n\n"
            "Попробуйте:  /random"
        )
        await update.message.reply_text(msg, parse_mode="HTML")
        return

    msg = "��  <b>Ваши закладки:</b>\n\n"
    buttons = []
    for i, ref in enumerate(bm, 1):
        su = int(ref.split(":")[0])
        ay = int(ref.split(":")[1])
        name = get_surah_name(su)
        msg += f"  {i}.  {name}  —  <code>{ref}</code>\n"
        buttons.append([
            InlineKeyboardButton(
                f"📖 {name} {ref}",
                callback_data=f"load_{su}_{ay}",
            ),
            InlineKeyboardButton(
                "🗑",
                callback_data=f"delbm_{su}_{ay}",
            ),
        ])

    msg += f"\n📌 Нажмите, чтобы открыть аят:"
    kb = InlineKeyboardMarkup(buttons) if buttons else None
    await update.message.reply_text(msg, parse_mode="HTML", reply_markup=kb)


async def handle_any_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle non-command text: auto-welcome or hint."""
    if not update.message or not update.message.text:
        return
    uid = update.effective_user.id

    if not user_data.user_exists(uid):
        user_data.ensure_user(uid)
        await update.message.reply_text(_WELCOME, parse_mode="HTML")
    else:
        await update.message.reply_text(
            "📖 Используйте:\n"
            "/random — случайный аят\n"
            "/hadith — хадис дня\n"
            "/bookmarks — закладки",
            parse_mode="HTML",
        )


# ═══════════════════════════════════════════
# 🔄  CALLBACK  HANDLERS
# ═══════════════════════════════════════════

async def handle_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    d = query.data

    if d == "noop":
        await query.answer()
        return
    if d.startswith("nav_"):
        await _cb_nav(query)
    elif d.startswith("bm_"):
        await _cb_bookmark(query)
    elif d.startswith("delbm_"):
        await _cb_delbookmark(query)
    elif d.startswith("load_"):
        await _cb_load_ayah(query)
    elif d == "more_hadith":
        await _cb_more_hadith(query)
    else:
        await query.answer("❓")


async def _cb_nav(query):
    """Navigate to prev/next ayah."""
    await query.answer()
    try:
        parts = query.data.split("_")
        su, ay = int(parts[1]), int(parts[2])
    except Exception:
        return
    uid = query.from_user.id
    data = fetch_ayah(su, ay)
    if not data:
        await query.answer("❌ Ошибка загрузки")
        return
    user_data.mark_ayah_read(uid, su, ay)
    msg = format_ayah_compact(data)
    kb = _ayah_keyboard(su, ay)
    await _safe_send(query, msg, keyboard=kb)


async def _cb_bookmark(query):
    """Add an ayah to bookmarks."""
    try:
        parts = query.data.split("_")
        su, ay = int(parts[1]), int(parts[2])
    except Exception:
        await query.answer("❌")
        return
    uid = query.from_user.id
    user_data.ensure_user(uid)
    if user_data.add_bookmark(uid, su, ay):
        name = get_surah_name(su)
        await query.answer(f"✅ {name} {su}:{ay} сохранён")
    else:
        await query.answer("📌 Уже в закладках!")


async def _cb_delbookmark(query):
    """Remove an ayah from bookmarks."""
    try:
        parts = query.data.split("_")
        su, ay = int(parts[1]), int(parts[2])
    except Exception:
        await query.answer("❌")
        return
    uid = query.from_user.id
    if user_data.remove_bookmark(uid, su, ay):
        await query.answer(f"🗑 {su}:{ay} удалён")
        # Refresh the bookmarks view
        bm = user_data.get_bookmarks(uid)
        if not bm:
            await query.edit_message_text(
                "🔖  <b>Закладки пусты</b>\n\n"
                "Попробуйте:  /random",
                parse_mode="HTML",
            )
        else:
            msg = "🔖  <b>Ваши закладки:</b>\n\n"
            buttons = []
            for i, ref in enumerate(bm, 1):
                s = int(ref.split(":")[0])
                a = int(ref.split(":")[1])
                name = get_surah_name(s)
                msg += f"  {i}.  {name}  —  <code>{ref}</code>\n"
                buttons.append([
                    InlineKeyboardButton(
                        f"📖 {name} {ref}",
                        callback_data=f"load_{s}_{a}",
                    ),
                    InlineKeyboardButton("🗑", callback_data=f"delbm_{s}_{a}"),
                ])
            msg += "\n📌 Нажмите, чтобы открыть аят:"
            await query.edit_message_text(
                msg, parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(buttons),
            )
    else:
        await query.answer("❌ Не найдено")


async def _cb_load_ayah(query):
    """Load a specific ayah from bookmarks."""
    await query.answer("📖 Загружаю…")
    try:
        parts = query.data.split("_")
        su, ay = int(parts[1]), int(parts[2])
    except Exception:
        return
    uid = query.from_user.id
    data = fetch_ayah(su, ay)
    if not data:
        await query.answer("❌ Ошибка загрузки")
        return
    user_data.mark_ayah_read(uid, su, ay)
    msg = format_ayah_compact(data)
    kb = _ayah_keyboard(su, ay)
    await query.message.reply_text(
        msg, parse_mode="HTML", reply_markup=kb)


async def _cb_more_hadith(query):
    """Fetch another random hadith."""
    await query.answer()
    h = fetch_random_hadith()
    msg = format_hadith_message(h)
    await _safe_send(query, msg, keyboard=_hadith_keyboard())


# ═══════════════════════════════════════════
# ⏰  РАСПИСАНИЕ  (ежедневные аяты)
# ═══════════════════════════════════════════

_scheduler: AsyncIOScheduler | None = None
_bot_app: Application | None = None


async def send_scheduled_message(app: Application):
    """Send a scheduled daily ayah + hadith to CHAT_ID."""
    try:
        logger.info("⏰ Scheduled message triggered")
        data = fetch_random_ayah()
        if not data:
            logger.error("Scheduled: fetch failed")
            return
        su, ay = data["surah_num"], data["ayah_num"]
        hadith = fetch_random_hadith()
        msg = format_ayah_compact(data, hadith)
        kb = _ayah_keyboard(su, ay)
        await app.bot.send_message(
            chat_id=CHAT_ID, text=msg[:4096],
            parse_mode="HTML", reply_markup=kb)
        logger.info("✅ Scheduled → %s:%s", su, ay)
    except Exception as e:
        logger.error("Scheduled error: %s", e)


# ═══════════════════════════════════════════
# 🌐  FLASK  WEB  SERVER
# ═══════════════════════════════════════════

flask_app = Flask(__name__, static_folder="webapp", static_url_path="/static")
CORS(flask_app)


@flask_app.after_request
def _add_headers(response):
    response.headers["ngrok-skip-browser-warning"] = "true"
    return response


@flask_app.route("/")
def serve_root():
    return send_from_directory("webapp", "index.html")


@flask_app.route("/webapp")
def serve_webapp():
    return send_from_directory("webapp", "index.html")


@flask_app.route("/webapp/<path:filename>")
def serve_webapp_file(filename):
    return send_from_directory("webapp", filename)


@flask_app.route("/api/tafsir")
def api_tafsir():
    """GET /api/tafsir?surah=1&ayah=1 — returns translated tafsir."""
    try:
        surah = int(flask_request.args.get("surah", 1))
        ayah = int(flask_request.args.get("ayah", 1))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid params"}), 400
    if not (1 <= surah <= 114):
        return jsonify({"error": "Surah 1-114"}), 400
    mx = get_ayah_count(surah)
    if not (1 <= ayah <= mx):
        return jsonify({"error": f"Ayah 1-{mx}"}), 400

    raw_qurtubi = get_full_tafsir(surah, ayah, "qurtubi")
    raw_qushairi = get_full_tafsir(surah, ayah, "qushairi")

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
        "lang": "ru",
        "translated": True,
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
# 🚀  ЗАПУСК
# ═══════════════════════════════════════════

async def main():
    global _scheduler, _bot_app

    _load_cache()

    logger.info("🤖 Starting Коран и Тафсир Bot…")
    logger.info("🌐 Web App URL: %s", WEBAPP_URL)

    flask_thread = threading.Thread(target=_run_flask, daemon=True)
    flask_thread.start()
    logger.info("🌐 Flask → %s:%s", FLASK_HOST, FLASK_PORT)

    app = Application.builder().token(BOT_TOKEN).build()
    _bot_app = app

    # 3 main commands
    app.add_handler(CommandHandler("random", cmd_random))
    app.add_handler(CommandHandler("hadith", cmd_hadith))
    app.add_handler(CommandHandler("bookmarks", cmd_bookmarks))
    # Legacy /start → same as /random
    app.add_handler(CommandHandler("start", cmd_random))
    # Callbacks
    app.add_handler(CallbackQueryHandler(handle_callback))
    # Any other text → auto-welcome or hint
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, handle_any_message))

    # APScheduler
    _scheduler = AsyncIOScheduler(
        job_defaults={"misfire_grace_time": 120},
    )
    for t in SCHEDULE_TIMES:
        hh, mm = map(int, t.split(":"))
        _scheduler.add_job(
            send_scheduled_message, "cron",
            hour=hh, minute=mm, args=[app],
            id=f"schedule_{hh:02d}{mm:02d}",
            replace_existing=True,
            misfire_grace_time=120,
        )

    await app.initialize()
    await app.start()
    logger.info("✅ Bot initialized")

    _scheduler.start()
    jobs = _scheduler.get_jobs()
    logger.info("📅 Scheduler: %d jobs", len(jobs))

    await app.bot.set_my_commands([
        BotCommand("random", "Случайный аят"),
        BotCommand("hadith", "Хадис дня"),
        BotCommand("bookmarks", "Мои закладки"),
    ])
    logger.info("📋 Bot menu set (3 commands)")

    await app.updater.start_polling()
    logger.info("✅ Bot running!  Ctrl+C to stop.")

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
