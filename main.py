#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
 Hadith Telegram Bot (Sahih Bukhari)
Delivers daily sequential Hadith, supports favorites, category search,
reminders, and multi-language (RU / EN / TR).
"""

import asyncio
import json
import logging
import os
import random

import requests
from deep_translator import GoogleTranslator
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from config import (
    BOT_TOKEN,
    CHAT_ID,
    AVAILABLE_LANGUAGES,
    HADITH_API_BASE,
    HADITH_SECTIONS,
)
import user_data

# 
#   LOGGING
# 

logging.basicConfig(
    format="%(asctime)s  %(name)-18s  %(levelname)-7s  %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("bot")

# 
#   i18n STRINGS
# 

_STRINGS = {
    "ru": {
        "welcome": (
            " <b>Ас-саляму алейкум!</b> \n\n"
            "Добро пожаловать в <b>Hadith Bot</b>! \n\n"
            " <b>Возможности:</b>\n"
            "   Ежедневный хадис в заданное время\n"
            "    Сохранение избранных хадисов\n"
            "    Поиск по ключевому слову\n"
            "    Личные напоминания\n"
            "    Язык: RU / EN / TR\n\n"
            " <b>Команды:</b>\n"
            "/hadith  Случайный хадис\n"
            "/hadith сабр  Хадис по теме\n"
            "/daily 08:30  Ежедневный хадис\n"
            "/dailyoff  Отключить ежедневный\n"
            "/fav  Сохранить последний \n"
            "/favorites  Мои избранные\n"
            "/unfav 1  Удалить #1 из избранных\n"
            "/remind 08:30  Напоминание\n"
            "/reminders  Мои напоминания\n"
            "/delremind 1  Удалить напоминание #1\n"
            "/lang  Сменить язык\n\n"
            " <i>Пусть этот бот приблизит вас к Сунне Пророка ﷺ.</i>"
        ),
        "hadith_title": " <b>Хадис из Сахих аль-Бухари</b>",
        "daily_hadith_title": " <b>Хадис дня</b>",
        "no_hadith": " Хадис не найден. Попробуйте другой запрос.",
        "fav_saved": " Хадис сохранён в избранном!",
        "fav_dup": " Уже в избранном!",
        "fav_none": " Нет последнего хадиса. Сначала запросите /hadith.",
        "favorites_empty": " Нет избранных. Используйте /fav после /hadith.",
        "favorites_title": " <b>Ваши избранные хадисы:</b>",
        "unfav_ok": " Хадис #{id} удалён из избранного.",
        "unfav_bad": " Нет хадиса #{id} в избранном.",
        "daily_set": " Ежедневный хадис установлен на <b>{t}</b>.",
        "daily_off": " Ежедневный хадис отключён.",
        "daily_none": "ℹ Ежедневный хадис не настроен. /daily HH:MM",
        "daily_current": " Ежедневный хадис: <b>{t}</b>.",
        "remind_ok": " Напоминание добавлено: <b>{t}</b>.",
        "remind_dup": " Напоминание на {t} уже есть.",
        "remind_bad": " Формат: <code>/remind HH:MM</code>",
        "reminders_empty": " Нет напоминаний. /remind HH:MM",
        "reminders_title": " <b>Ваши напоминания:</b>",
        "delremind_ok": " Напоминание #{i} удалено.",
        "delremind_bad": " Нет напоминания #{i}.",
        "delremind_help": "<code>/delremind 1</code> или <code>/delremind all</code>",
        "deleted_all": " Все напоминания удалены ({n}).",
        "more_hadith": " Ещё хадис",
        "save_fav": " В избранное",
        "lang_set": " Язык изменён.",
        "bad_time": " Формат времени: <code>HH:MM</code>",
        "loading": " Загружаю хадис",
    },
    "en": {
        "welcome": (
            " <b>As-salamu alaykum!</b> \n\n"
            "Welcome to <b>Hadith Bot</b>! \n\n"
            " <b>Features:</b>\n"
            "   Daily hadith at a fixed time\n"
            "    Save favourite hadiths\n"
            "    Search by keyword\n"
            "    Personal reminders\n"
            "    Language: RU / EN / TR\n\n"
            " <b>Commands:</b>\n"
            "/hadith  Random hadith\n"
            "/hadith sabr  Hadith by topic\n"
            "/daily 08:30  Set daily hadith\n"
            "/dailyoff  Disable daily\n"
            "/fav  Save last hadith \n"
            "/favorites  My favourites\n"
            "/unfav 1  Remove favourite #1\n"
            "/remind 08:30  Set reminder\n"
            "/reminders  My reminders\n"
            "/delremind 1  Delete reminder #1\n"
            "/lang  Change language\n\n"
            " <i>May this bot bring you closer to the Sunnah of the Prophet ﷺ.</i>"
        ),
        "hadith_title": " <b>Hadith from Sahih al-Bukhari</b>",
        "daily_hadith_title": " <b>Hadith of the Day</b>",
        "no_hadith": " No hadith found. Try a different query.",
        "fav_saved": " Hadith saved to favourites!",
        "fav_dup": " Already in favourites!",
        "fav_none": " No recent hadith. Request /hadith first.",
        "favorites_empty": " No favourites yet. Use /fav after /hadith.",
        "favorites_title": " <b>Your favourite hadiths:</b>",
        "unfav_ok": " Hadith #{id} removed from favourites.",
        "unfav_bad": " No hadith #{id} in favourites.",
        "daily_set": " Daily hadith set for <b>{t}</b>.",
        "daily_off": " Daily hadith disabled.",
        "daily_none": "ℹ Daily hadith not set. Use /daily HH:MM",
        "daily_current": " Daily hadith: <b>{t}</b>.",
        "remind_ok": " Reminder added: <b>{t}</b>.",
        "remind_dup": " Reminder at {t} already exists.",
        "remind_bad": " Format: <code>/remind HH:MM</code>",
        "reminders_empty": " No reminders. Use /remind HH:MM",
        "reminders_title": " <b>Your reminders:</b>",
        "delremind_ok": " Reminder #{i} removed.",
        "delremind_bad": " No reminder #{i}.",
        "delremind_help": "<code>/delremind 1</code> or <code>/delremind all</code>",
        "deleted_all": " All reminders deleted ({n}).",
        "more_hadith": " Another hadith",
        "save_fav": " Save to favourites",
        "lang_set": " Language changed.",
        "bad_time": " Time format: <code>HH:MM</code>",
        "loading": " Loading hadith",
    },
    "tr": {
        "welcome": (
            " <b>Es-selamu aleyküm!</b> \n\n"
            "<b>Hadith Bot</b>'a hoş geldiniz! \n\n"
            " <b>Özellikler:</b>\n"
            "   Belirli saatte günlük hadis\n"
            "    Favori hadis kaydetme\n"
            "    Anahtar kelime ile arama\n"
            "    Kişisel hatırlatmalar\n"
            "    Dil: RU / EN / TR\n\n"
            " <b>Komutlar:</b>\n"
            "/hadith  Rastgele hadis\n"
            "/hadith sabır  Konuya göre hadis\n"
            "/daily 08:30  Günlük hadis saati\n"
            "/dailyoff  Günlük hadisi kapat\n"
            "/fav  Son hadisi favori yap \n"
            "/favorites  Favorilerim\n"
            "/unfav 1  #1 favoriyi sil\n"
            "/remind 08:30  Hatırlatma ekle\n"
            "/reminders  Hatırlatmalarım\n"
            "/delremind 1  #1 hatırlatmayı sil\n"
            "/lang  Dili değiştir\n\n"
            " <i>Bu bot sizi Peygamber'in ﷺ Sünnet'ine yaklaştırsın.</i>"
        ),
        "hadith_title": " <b>Sahih el-Buhari'den Hadis</b>",
        "daily_hadith_title": " <b>Günün Hadisi</b>",
        "no_hadith": " Hadis bulunamadı. Farklı bir arama deneyin.",
        "fav_saved": " Hadis favorilere kaydedildi!",
        "fav_dup": " Zaten favorilerde!",
        "fav_none": " Son hadis yok. Önce /hadith isteyin.",
        "favorites_empty": " Henüz favori yok. /hadith sonrası /fav kullanın.",
        "favorites_title": " <b>Favori hadisleriniz:</b>",
        "unfav_ok": " #{id} numaralı hadis favorilerden silindi.",
        "unfav_bad": " Favorilerde #{id} yok.",
        "daily_set": " Günlük hadis <b>{t}</b> olarak ayarlandı.",
        "daily_off": " Günlük hadis devre dışı bırakıldı.",
        "daily_none": "ℹ Günlük hadis ayarlanmamış. /daily SS:DD",
        "daily_current": " Günlük hadis: <b>{t}</b>.",
        "remind_ok": " Hatırlatma eklendi: <b>{t}</b>.",
        "remind_dup": " {t} için zaten hatırlatma var.",
        "remind_bad": " Format: <code>/remind SS:DD</code>",
        "reminders_empty": " Hatırlatma yok. /remind SS:DD kullanın.",
        "reminders_title": " <b>Hatırlatmalarınız:</b>",
        "delremind_ok": " #{i} hatırlatması silindi.",
        "delremind_bad": " #{i} hatırlatması yok.",
        "delremind_help": "<code>/delremind 1</code> veya <code>/delremind all</code>",
        "deleted_all": " Tüm hatırlatmalar silindi ({n}).",
        "more_hadith": " Başka hadis",
        "save_fav": " Favorilere ekle",
        "lang_set": " Dil değiştirildi.",
        "bad_time": " Saat formatı: <code>SS:DD</code>",
        "loading": " Hadis yükleniyor",
    },
}


def S(lang: str) -> dict:
    return _STRINGS.get(lang, _STRINGS["en"])


# 
#   HADITH  API
# 

def _fetch_section(section: int) -> list[dict]:
    """Fetch all hadiths from a Bukhari section (1-100)."""
    try:
        url = f"{HADITH_API_BASE}/{section}.json"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json().get("hadiths", [])
    except Exception as e:
        logger.error("Hadith API section %d error: %s", section, e)
        return []


def fetch_random_hadith() -> dict:
    """Fetch one random hadith from Sahih Bukhari."""
    section = random.randint(1, HADITH_SECTIONS)
    hadiths = _fetch_section(section)
    if not hadiths:
        return _fallback_hadith()
    h = random.choice(hadiths)
    return _parse_hadith(h, section)


def fetch_sequential_hadith(index: int) -> dict:
    """Fetch hadith by sequential index across all sections."""
    section = (index % HADITH_SECTIONS) + 1
    hadiths = _fetch_section(section)
    if not hadiths:
        return _fallback_hadith()
    h = hadiths[index % max(len(hadiths), 1)]
    return _parse_hadith(h, section)


def fetch_hadith_by_keyword(keyword: str) -> dict | None:
    """Search a few random sections for a hadith containing the keyword."""
    kw = keyword.lower()
    sections = random.sample(range(1, HADITH_SECTIONS + 1), min(10, HADITH_SECTIONS))
    for section in sections:
        hadiths = _fetch_section(section)
        matches = [h for h in hadiths if kw in h.get("text", "").lower()]
        if matches:
            return _parse_hadith(random.choice(matches), section)
    return None


def _parse_hadith(h: dict, section: int) -> dict:
    num = h.get("hadithnumber", "?")
    ref_data = h.get("reference", {})
    book = ref_data.get("book", section) if isinstance(ref_data, dict) else section
    return {
        "text": h.get("text", ""),
        "reference": f"Sahih al-Bukhari  Book {book}, Hadith {num}",
    }


def _fallback_hadith() -> dict:
    return {
        "text": "Actions are judged by intentions, so each man will have what he intended.",
        "reference": "Sahih al-Bukhari, Hadith 1",
    }


# 
#   TRANSLATION
# 

def translate_hadith(text: str, lang: str) -> str:
    """Translate hadith text from English to the target language."""
    if lang == "en" or not text:
        return text
    try:
        return GoogleTranslator(source="en", target=lang).translate(text[:4000]) or text
    except Exception as e:
        logger.warning("Translation error (%s): %s", lang, e)
        return text


# 
#   MESSAGE FORMATTING
# 

def format_hadith(h: dict, lang: str, title_key: str = "hadith_title") -> str:
    s = S(lang)
    txt = translate_hadith(h["text"], lang)
    return f"{s[title_key]}\n\n<i>{txt}</i>\n\n <i>{h['reference']}</i>"


def hadith_keyboard(lang: str) -> InlineKeyboardMarkup:
    s = S(lang)
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(s["more_hadith"], callback_data="more_hadith"),
        InlineKeyboardButton(s["save_fav"], callback_data="save_fav"),
    ]])


# 
#   BOT COMMANDS
# 

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = user_data.get_language(update.effective_user.id)
    await update.message.reply_text(S(lang)["welcome"], parse_mode="HTML")


async def cmd_hadith(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = user_data.get_language(uid)
    s = S(lang)

    wait = await update.message.reply_text(s["loading"])

    if ctx.args:
        keyword = " ".join(ctx.args)
        h = await asyncio.to_thread(fetch_hadith_by_keyword, keyword)
        if not h:
            await wait.edit_text(s["no_hadith"])
            return
    else:
        h = await asyncio.to_thread(fetch_random_hadith)

    user_data.set_last_hadith(uid, h["text"], h["reference"])
    msg = await asyncio.to_thread(format_hadith, h, lang)
    await wait.edit_text(msg, parse_mode="HTML", reply_markup=hadith_keyboard(lang))


async def cmd_fav(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = user_data.get_language(uid)
    s = S(lang)

    last = user_data.get_last_hadith(uid)
    if not last:
        await update.message.reply_text(s["fav_none"])
        return

    result = user_data.add_favorite(uid, last["text"], last["reference"])
    if result:
        await update.message.reply_text(s["fav_saved"])
    else:
        await update.message.reply_text(s["fav_dup"])


async def cmd_favorites(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = user_data.get_language(uid)
    s = S(lang)

    favs = user_data.get_favorites(uid)
    if not favs:
        await update.message.reply_text(s["favorites_empty"])
        return

    msg = s["favorites_title"] + "\n\n"
    for fav in favs:
        preview = fav["text"][:120] + "" if len(fav["text"]) > 120 else fav["text"]
        msg += f"<b>#{fav['id']}</b> {fav['reference']}\n<i>{preview}</i>\n\n"
    msg += " /unfav &lt;id&gt;"
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_unfav(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = user_data.get_language(uid)
    s = S(lang)

    if not ctx.args:
        await update.message.reply_text("Usage: /unfav <id>")
        return
    try:
        fav_id = int(ctx.args[0])
    except ValueError:
        await update.message.reply_text("Usage: /unfav <id>")
        return

    if user_data.remove_favorite(uid, fav_id):
        await update.message.reply_text(s["unfav_ok"].format(id=fav_id))
    else:
        await update.message.reply_text(s["unfav_bad"].format(id=fav_id))


async def cmd_daily(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = user_data.get_language(uid)
    s = S(lang)

    if not ctx.args:
        t = user_data.get_daily_time(uid)
        if t:
            await update.message.reply_text(s["daily_current"].format(t=t), parse_mode="HTML")
        else:
            await update.message.reply_text(s["daily_none"])
        return

    time_str = ctx.args[0]
    if not _valid_time(time_str):
        await update.message.reply_text(s["bad_time"], parse_mode="HTML")
        return

    time_str = _norm_time(time_str)
    user_data.set_daily_time(uid, time_str)
    _register_daily_job(uid, time_str, ctx.application)
    await update.message.reply_text(s["daily_set"].format(t=time_str), parse_mode="HTML")


async def cmd_dailyoff(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = user_data.get_language(uid)
    _remove_daily_job(uid)
    user_data.disable_daily(uid)
    await update.message.reply_text(S(lang)["daily_off"])


async def cmd_remind(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = user_data.get_language(uid)
    s = S(lang)

    if not ctx.args:
        await update.message.reply_text(s["remind_bad"], parse_mode="HTML")
        return

    time_str = ctx.args[0]
    if not _valid_time(time_str):
        await update.message.reply_text(s["bad_time"], parse_mode="HTML")
        return

    time_str = _norm_time(time_str)
    label = " ".join(ctx.args[1:]) if len(ctx.args) > 1 else ""
    result = user_data.add_reminder(uid, time_str, label)
    if result is None:
        await update.message.reply_text(s["remind_dup"].format(t=time_str))
        return
    _register_reminder_job(uid, result, ctx.application)
    await update.message.reply_text(s["remind_ok"].format(t=time_str), parse_mode="HTML")


async def cmd_reminders(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = user_data.get_language(uid)
    s = S(lang)

    rems = user_data.get_reminders(uid)
    if not rems:
        await update.message.reply_text(s["reminders_empty"])
        return

    msg = s["reminders_title"] + "\n\n"
    for i, r in enumerate(rems, 1):
        lbl = f"   {r['label']}" if r.get("label") else ""
        msg += f"  {i}. <b>{r['time']}</b>{lbl}\n"
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
        rems = user_data.get_reminders(uid)
        _remove_all_reminder_jobs(uid, rems)
        count = user_data.clear_reminders(uid)
        await update.message.reply_text(s["deleted_all"].format(n=count))
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
        await update.message.reply_text(s["delremind_ok"].format(i=idx))
    else:
        await update.message.reply_text(s["delremind_bad"].format(i=idx))


async def cmd_lang(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    cur = user_data.get_language(uid)
    kb = [[InlineKeyboardButton(
        f"{label}{' ' if code == cur else ''}",
        callback_data=f"setlang_{code}",
    )] for code, label in AVAILABLE_LANGUAGES.items()]
    await update.message.reply_text(
        f" <b>{AVAILABLE_LANGUAGES.get(cur, cur)}</b>",
        parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))


# 
#   CALLBACKS
# 

async def handle_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    d = query.data

    if d == "more_hadith":
        await query.answer()
        uid = query.from_user.id
        lang = user_data.get_language(uid)
        h = await asyncio.to_thread(fetch_random_hadith)
        user_data.set_last_hadith(uid, h["text"], h["reference"])
        msg = await asyncio.to_thread(format_hadith, h, lang)
        try:
            await query.edit_message_text(msg, parse_mode="HTML",
                                          reply_markup=hadith_keyboard(lang))
        except Exception:
            await query.message.reply_text(msg, parse_mode="HTML",
                                           reply_markup=hadith_keyboard(lang))

    elif d == "save_fav":
        uid = query.from_user.id
        lang = user_data.get_language(uid)
        s = S(lang)
        last = user_data.get_last_hadith(uid)
        if not last:
            await query.answer(s["fav_none"][:200])
            return
        result = user_data.add_favorite(uid, last["text"], last["reference"])
        await query.answer(s["fav_saved"] if result else s["fav_dup"])

    elif d.startswith("setlang_"):
        lang = d.replace("setlang_", "")
        uid = query.from_user.id
        user_data.set_language(uid, lang)
        lb = AVAILABLE_LANGUAGES.get(lang, lang)
        await query.answer(f" {lb}")
        kb = [[InlineKeyboardButton(
            f"{label}{' ' if code == lang else ''}",
            callback_data=f"setlang_{code}",
        )] for code, label in AVAILABLE_LANGUAGES.items()]
        await query.edit_message_text(
            f" <b>{lb}</b>", parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(kb))

    else:
        await query.answer()


# 
#   SCHEDULER
# 

_scheduler: AsyncIOScheduler | None = None
_bot_app: Application | None = None


async def _send_daily_hadith(app: Application, uid: int):
    try:
        lang = user_data.get_language(uid)
        idx = user_data.get_daily_index(uid)
        h = await asyncio.to_thread(fetch_sequential_hadith, idx)
        user_data.increment_daily_index(uid)
        user_data.set_last_hadith(uid, h["text"], h["reference"])
        msg = await asyncio.to_thread(format_hadith, h, lang, "daily_hadith_title")
        await app.bot.send_message(
            chat_id=uid, text=msg[:4096],
            parse_mode="HTML", reply_markup=hadith_keyboard(lang))
        logger.info(" Daily hadith  uid=%s idx=%s", uid, idx)
    except Exception as e:
        logger.error("Daily hadith error uid=%s: %s", uid, e)


async def _send_reminder(app: Application, uid: int, label: str):
    try:
        lang = user_data.get_language(uid)
        s = S(lang)
        lbl = f"\n <i>{label}</i>" if label else ""
        h = await asyncio.to_thread(fetch_random_hadith)
        user_data.set_last_hadith(uid, h["text"], h["reference"])
        msg = await asyncio.to_thread(format_hadith, h, lang)
        note = f" <b>Reminder</b>{lbl}\n\n" + msg
        await app.bot.send_message(
            chat_id=uid, text=note[:4096],
            parse_mode="HTML", reply_markup=hadith_keyboard(lang))
        logger.info(" Reminder  uid=%s", uid)
    except Exception as e:
        logger.error("Reminder error uid=%s: %s", uid, e)


def _daily_job_id(uid) -> str:
    return f"daily_{uid}"


def _reminder_job_id(uid, time_str: str) -> str:
    return f"remind_{uid}_{time_str}"


def _register_daily_job(uid, time_str: str, app: Application):
    if not _scheduler:
        return
    jid = _daily_job_id(uid)
    hh, mm = map(int, time_str.split(":"))
    try:
        _scheduler.remove_job(jid)
    except Exception:
        pass
    _scheduler.add_job(
        _send_daily_hadith, "cron", hour=hh, minute=mm,
        args=[app, int(uid)], id=jid)


def _remove_daily_job(uid):
    if not _scheduler:
        return
    try:
        _scheduler.remove_job(_daily_job_id(uid))
    except Exception:
        pass


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
        _send_reminder, "cron", hour=hh, minute=mm,
        args=[app, int(uid), reminder.get("label", "")],
        id=jid)


def _remove_reminder_job(uid, time_str: str):
    if not _scheduler:
        return
    try:
        _scheduler.remove_job(_reminder_job_id(uid, time_str))
    except Exception:
        pass


def _remove_all_reminder_jobs(uid, reminders: list):
    for r in reminders:
        _remove_reminder_job(uid, r["time"])


def _load_all_jobs(app: Application):
    # Daily jobs
    daily_users = user_data.get_all_daily_users()
    for uid, t in daily_users.items():
        _register_daily_job(uid, t, app)
    # Reminder jobs
    all_rems = user_data.get_all_reminders()
    count = 0
    for uid, rems in all_rems.items():
        for r in rems:
            _register_reminder_job(uid, r, app)
            count += 1
    logger.info(" Loaded %d daily users + %d reminders", len(daily_users), count)


# 
#   HELPERS
# 

def _valid_time(t: str) -> bool:
    try:
        hh, mm = t.split(":")
        return 0 <= int(hh) <= 23 and 0 <= int(mm) <= 59
    except Exception:
        return False


def _norm_time(t: str) -> str:
    hh, mm = t.split(":")
    return f"{int(hh):02d}:{int(mm):02d}"


# 
#   MAIN
# 

async def main():
    global _scheduler, _bot_app

    logger.info(" Starting Hadith Bot")

    app = Application.builder().token(BOT_TOKEN).build()
    _bot_app = app

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("hadith", cmd_hadith))
    app.add_handler(CommandHandler("fav", cmd_fav))
    app.add_handler(CommandHandler("favorites", cmd_favorites))
    app.add_handler(CommandHandler("unfav", cmd_unfav))
    app.add_handler(CommandHandler("daily", cmd_daily))
    app.add_handler(CommandHandler("dailyoff", cmd_dailyoff))
    app.add_handler(CommandHandler("remind", cmd_remind))
    app.add_handler(CommandHandler("reminders", cmd_reminders))
    app.add_handler(CommandHandler("delremind", cmd_delremind))
    app.add_handler(CommandHandler("lang", cmd_lang))
    app.add_handler(CallbackQueryHandler(handle_callback))

    async def _error_handler(update, context):
        logger.error("Unhandled error: %s", context.error)
    app.add_error_handler(_error_handler)

    _scheduler = AsyncIOScheduler()
    _scheduler.start()

    await app.initialize()
    await app.start()
    _load_all_jobs(app)

    await app.bot.set_my_commands([
        BotCommand("hadith", "Random / search hadith"),
        BotCommand("fav", "Save last hadith "),
        BotCommand("favorites", "My favourites"),
        BotCommand("unfav", "Remove favourite /unfav <id>"),
        BotCommand("daily", "Set daily hadith time"),
        BotCommand("dailyoff", "Disable daily hadith"),
        BotCommand("remind", "Add reminder /remind HH:MM"),
        BotCommand("reminders", "My reminders"),
        BotCommand("delremind", "Delete reminder"),
        BotCommand("lang", "Change language"),
        BotCommand("start", "Welcome / help"),
    ])
    logger.info(" Bot running! Ctrl+C to stop.")

    await app.updater.start_polling()
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info(" Shutting down")
        _scheduler.shutdown()
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info(" Stopped.")