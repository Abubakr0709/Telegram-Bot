#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Hadith Telegram Bot (Sahih Bukhari)
Delivers daily sequential Hadith, supports favorites, category search,
guided notifications, image cards, and multi-language (RU / EN / TR).
"""

import asyncio
import logging
import random

import requests
from deep_translator import GoogleTranslator
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand,
    ForceReply,
)
from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from config import (
    BOT_TOKEN,
    AVAILABLE_LANGUAGES,
    HADITH_API_BASE,
    HADITH_SECTIONS,
    PEXELS_API_KEY,
)
import user_data
from islamic_images import fetch_islamic_photo_url

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
            "  Хадисы с красивыми карточками\n"
            "  Ежедневная отправка по времени\n"
            "  Избранные хадисы\n"
            "  Язык: RU / EN / TR\n\n"
            "Нажмите кнопку ниже, чтобы открыть меню действий.\n\n"
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
        "daily_none": " Ежедневный хадис не настроен.",
        "daily_current": " Ежедневный хадис: <b>{t}</b>.",
        "more_hadith": " Ещё хадис",
        "save_fav": " В избранное",
        "open_menu": " Меню",
        "get_hadith": " Хадис",
        "notifications_btn": " Уведомления",
        "favorites_btn": " Избранное",
        "language_btn": " Язык",
        "menu_title": " <b>Меню</b>\nВыберите действие:",
        "notifications_title_on": " <b>Уведомления</b>\nСтатус: <b>Вкл ({t})</b>",
        "notifications_title_off": " <b>Уведомления</b>\nСтатус: <b>Выкл</b>",
        "set_time_btn": " Установить время",
        "turn_off_btn": " Выключить",
        "back_btn": " Назад",
        "set_time_prompt": " Введите время в формате <code>HH:MM</code>:",
        "set_time_again": " Неверный формат. Введите <code>HH:MM</code>:",
        "deprecated_scheduler": "Эта команда устарела. Используйте кнопку <b>Уведомления</b>.",
        "lang_set": " Язык изменён.",
        "bad_time": " Формат времени: <code>HH:MM</code>",
        "loading": " Загружаю хадис",
    },
    "en": {
        "welcome": (
            " <b>As-salamu alaykum!</b> \n\n"
            "Welcome to <b>Hadith Bot</b>! \n\n"
            " <b>Features:</b>\n"
            "  Hadith cards with clean visuals\n"
            "  Daily delivery at your chosen time\n"
            "  Favourite hadith list\n"
            "  Language: RU / EN / TR\n\n"
            "Tap the button below to open actions.\n\n"
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
        "daily_none": " Daily hadith is not set.",
        "daily_current": " Daily hadith: <b>{t}</b>.",
        "more_hadith": " Another hadith",
        "save_fav": " Save to favourites",
        "open_menu": " Menu",
        "get_hadith": " Get Hadith",
        "notifications_btn": " Notifications",
        "favorites_btn": " Favorites",
        "language_btn": " Language",
        "menu_title": " <b>Menu</b>\nChoose an action:",
        "notifications_title_on": " <b>Notifications</b>\nStatus: <b>On ({t})</b>",
        "notifications_title_off": " <b>Notifications</b>\nStatus: <b>Off</b>",
        "set_time_btn": " Set Time",
        "turn_off_btn": " Turn Off",
        "back_btn": " Back",
        "set_time_prompt": " Send time in <code>HH:MM</code> format:",
        "set_time_again": " Invalid format. Send <code>HH:MM</code>:",
        "deprecated_scheduler": "This command is deprecated. Use the <b>Notifications</b> button.",
        "lang_set": " Language changed.",
        "bad_time": " Time format: <code>HH:MM</code>",
        "loading": " Loading hadith",
    },
    "tr": {
        "welcome": (
            " <b>Es-selamu aleyküm!</b> \n\n"
            "<b>Hadith Bot</b>'a hoş geldiniz! \n\n"
            " <b>Özellikler:</b>\n"
            "  Temiz tasarımlı hadis kartları\n"
            "  Seçtiğiniz saatte günlük gönderim\n"
            "  Favori hadis listesi\n"
            "  Dil: RU / EN / TR\n\n"
            "Aşağıdaki düğmeyle menüyü açın.\n\n"
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
        "daily_none": " Günlük hadis ayarlanmadı.",
        "daily_current": " Günlük hadis: <b>{t}</b>.",
        "more_hadith": " Başka hadis",
        "save_fav": " Favorilere ekle",
        "open_menu": " Menü",
        "get_hadith": " Hadis Getir",
        "notifications_btn": " Bildirimler",
        "favorites_btn": " Favoriler",
        "language_btn": " Dil",
        "menu_title": " <b>Menü</b>\nBir işlem seçin:",
        "notifications_title_on": " <b>Bildirimler</b>\nDurum: <b>Açık ({t})</b>",
        "notifications_title_off": " <b>Bildirimler</b>\nDurum: <b>Kapalı</b>",
        "set_time_btn": " Saat Ayarla",
        "turn_off_btn": " Kapat",
        "back_btn": " Geri",
        "set_time_prompt": " Saati <code>HH:MM</code> formatında gönderin:",
        "set_time_again": " Geçersiz format. <code>HH:MM</code> gönderin:",
        "deprecated_scheduler": "Bu komut artık kullanılmıyor. <b>Bildirimler</b> düğmesini kullanın.",
        "lang_set": " Dil değiştirildi.",
        "bad_time": " Saat formatı: <code>HH:MM</code>",
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
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(s["more_hadith"], callback_data="more_hadith"),
            InlineKeyboardButton(s["save_fav"], callback_data="save_fav"),
        ],
        [InlineKeyboardButton(s["open_menu"], callback_data="nav_menu")],
    ])


def main_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    s = S(lang)
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(s["get_hadith"], callback_data="nav_get_hadith")],
        [InlineKeyboardButton(s["notifications_btn"], callback_data="nav_notifications")],
        [
            InlineKeyboardButton(s["favorites_btn"], callback_data="nav_favorites"),
            InlineKeyboardButton(s["language_btn"], callback_data="nav_lang"),
        ],
    ])


def notifications_keyboard(lang: str, has_daily: bool) -> InlineKeyboardMarkup:
    s = S(lang)
    rows = [[InlineKeyboardButton(s["set_time_btn"], callback_data="notif_set_time")]]
    if has_daily:
        rows.append([InlineKeyboardButton(s["turn_off_btn"], callback_data="notif_turn_off")])
    rows.append([InlineKeyboardButton(s["back_btn"], callback_data="nav_menu")])
    return InlineKeyboardMarkup(rows)


def language_keyboard(active_lang: str) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(
        f"{label}{' ' if code == active_lang else ''}",
        callback_data=f"setlang_{code}",
    )] for code, label in AVAILABLE_LANGUAGES.items()]
    rows.append([InlineKeyboardButton(S(active_lang)["back_btn"], callback_data="nav_menu")])
    return InlineKeyboardMarkup(rows)


async def _send_hadith_card_or_text(
    bot,
    chat_id: int,
    h: dict,
    lang: str,
    title_key: str = "hadith_title",
    reply_markup: InlineKeyboardMarkup | None = None,
):
    translated = await asyncio.to_thread(translate_hadith, h["text"], lang)
    photo_url = await asyncio.to_thread(fetch_islamic_photo_url, PEXELS_API_KEY)
    try:
        if photo_url:
            await bot.send_photo(chat_id=chat_id, photo=photo_url)
    except Exception as e:
        logger.warning("Photo delivery failed, continuing with text: %s", e)

    msg = f"{S(lang)[title_key]}\n\n<i>{translated}</i>\n\n <i>{h['reference']}</i>"
    await bot.send_message(
        chat_id=chat_id,
        text=msg[:4096],
        parse_mode="HTML",
        reply_markup=reply_markup,
    )


# 
#   BOT COMMANDS
# 

_pending_daily_time: set[int] = set()


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = user_data.get_language(update.effective_user.id)
    await update.message.reply_text(
        S(lang)["welcome"],
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(lang),
    )


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
    await wait.delete()
    await _send_hadith_card_or_text(
        ctx.bot, update.effective_chat.id, h, lang, reply_markup=hadith_keyboard(lang)
    )


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
    await _send_scheduler_deprecated(update, ctx)


async def cmd_dailyoff(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await _send_scheduler_deprecated(update, ctx)


async def cmd_remind(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await _send_scheduler_deprecated(update, ctx)


async def cmd_reminders(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await _send_scheduler_deprecated(update, ctx)


async def cmd_delremind(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await _send_scheduler_deprecated(update, ctx)


async def cmd_lang(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    cur = user_data.get_language(uid)
    await update.message.reply_text(
        f" <b>{AVAILABLE_LANGUAGES.get(cur, cur)}</b>",
        parse_mode="HTML",
        reply_markup=language_keyboard(cur),
    )


async def handle_time_reply(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    uid = update.effective_user.id
    if uid not in _pending_daily_time:
        return

    lang = user_data.get_language(uid)
    s = S(lang)
    time_str = (update.message.text or "").strip()
    if not _valid_time(time_str):
        await update.message.reply_text(
            s["set_time_again"],
            parse_mode="HTML",
            reply_markup=ForceReply(selective=True),
        )
        return

    time_str = _norm_time(time_str)
    user_data.set_daily_time(uid, time_str)
    _register_daily_job(uid, time_str, ctx.application)
    _pending_daily_time.discard(uid)
    await update.message.reply_text(s["daily_set"].format(t=time_str), parse_mode="HTML")
    await update.message.reply_text(
        s["notifications_title_on"].format(t=time_str),
        parse_mode="HTML",
        reply_markup=notifications_keyboard(lang, has_daily=True),
    )


async def _send_scheduler_deprecated(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = user_data.get_language(uid)
    await update.message.reply_text(
        S(lang)["deprecated_scheduler"],
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(S(lang)["notifications_btn"], callback_data="nav_notifications")
        ]]),
    )


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
        await _send_hadith_card_or_text(
            ctx.bot, query.message.chat_id, h, lang, reply_markup=hadith_keyboard(lang)
        )

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

    elif d == "nav_menu":
        uid = query.from_user.id
        lang = user_data.get_language(uid)
        await query.answer()
        try:
            await query.edit_message_text(
                S(lang)["menu_title"],
                parse_mode="HTML",
                reply_markup=main_menu_keyboard(lang),
            )
        except Exception:
            await query.message.reply_text(
                S(lang)["menu_title"],
                parse_mode="HTML",
                reply_markup=main_menu_keyboard(lang),
            )

    elif d == "nav_get_hadith":
        await query.answer()
        uid = query.from_user.id
        lang = user_data.get_language(uid)
        h = await asyncio.to_thread(fetch_random_hadith)
        user_data.set_last_hadith(uid, h["text"], h["reference"])
        await _send_hadith_card_or_text(
            ctx.bot, query.message.chat_id, h, lang, reply_markup=hadith_keyboard(lang)
        )

    elif d == "nav_notifications":
        await query.answer()
        uid = query.from_user.id
        lang = user_data.get_language(uid)
        t = user_data.get_daily_time(uid)
        text = S(lang)["notifications_title_on"].format(t=t) if t else S(lang)["notifications_title_off"]
        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=notifications_keyboard(lang, has_daily=bool(t)),
        )

    elif d == "notif_set_time":
        await query.answer()
        uid = query.from_user.id
        lang = user_data.get_language(uid)
        _pending_daily_time.add(uid)
        await query.message.reply_text(
            S(lang)["set_time_prompt"],
            parse_mode="HTML",
            reply_markup=ForceReply(selective=True),
        )

    elif d == "notif_turn_off":
        await query.answer()
        uid = query.from_user.id
        lang = user_data.get_language(uid)
        _remove_daily_job(uid)
        user_data.disable_daily(uid)
        _pending_daily_time.discard(uid)
        await query.edit_message_text(
            S(lang)["notifications_title_off"],
            parse_mode="HTML",
            reply_markup=notifications_keyboard(lang, has_daily=False),
        )

    elif d == "nav_favorites":
        await query.answer()
        uid = query.from_user.id
        lang = user_data.get_language(uid)
        s = S(lang)
        favs = user_data.get_favorites(uid)
        if not favs:
            await query.message.reply_text(s["favorites_empty"])
            return
        msg = s["favorites_title"] + "\n\n"
        for fav in favs:
            preview = fav["text"][:120] + "" if len(fav["text"]) > 120 else fav["text"]
            msg += f"<b>#{fav['id']}</b> {fav['reference']}\n<i>{preview}</i>\n\n"
        msg += " /unfav &lt;id&gt;"
        await query.message.reply_text(msg, parse_mode="HTML")

    elif d == "nav_lang":
        await query.answer()
        uid = query.from_user.id
        cur = user_data.get_language(uid)
        await query.edit_message_text(
            f" <b>{AVAILABLE_LANGUAGES.get(cur, cur)}</b>",
            parse_mode="HTML",
            reply_markup=language_keyboard(cur),
        )

    elif d.startswith("setlang_"):
        lang = d.replace("setlang_", "")
        uid = query.from_user.id
        user_data.set_language(uid, lang)
        lb = AVAILABLE_LANGUAGES.get(lang, lang)
        await query.answer(f" {lb}")
        await query.edit_message_text(
            f" <b>{lb}</b>", parse_mode="HTML",
            reply_markup=language_keyboard(lang),
        )

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
        await _send_hadith_card_or_text(
            app.bot, uid, h, lang, title_key="daily_hadith_title", reply_markup=hadith_keyboard(lang)
        )
        logger.info(" Daily hadith  uid=%s idx=%s", uid, idx)
    except Exception as e:
        logger.error("Daily hadith error uid=%s: %s", uid, e)


def _daily_job_id(uid) -> str:
    return f"daily_{uid}"


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


def _load_all_jobs(app: Application):
    daily_users = user_data.get_all_daily_users()
    for uid, t in daily_users.items():
        _register_daily_job(uid, t, app)
    logger.info(" Loaded %d daily users", len(daily_users))


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
    app.add_handler(MessageHandler(filters.TEXT & filters.REPLY, handle_time_reply))
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
        BotCommand("favorites", "My favourites"),
        BotCommand("unfav", "Remove favourite /unfav <id>"),
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
