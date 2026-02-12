#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🕌 Quran & Tafsir Telegram Bot
────────────────────────────────
• Local tafsir (al-Qurtubi + al-Qushairi)
• Yandex Free Translation (no API key)
• Russian UI · Multi-language (RU / EN / TR)
• Bookmarks · Reading progress · Streaks
• ⬅️ ➡️ Ayah navigation
• Scheduled daily delivery
"""

import asyncio
import logging
import random

import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from yandexfreetranslate import YandexFreeTranslate
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import (
    BOT_TOKEN,
    CHAT_ID,
    SCHEDULE_TIMES,
    AVAILABLE_TRANSLATIONS,
    QURAN_API_BASE,
    HADITH_API,
    QURAN_EDITIONS,
    DEFAULT_TRANSLATION,
)
from tafsir_loader import (
    get_tafsir_for_ayah,
    search_tafsir,
    get_surah_name,
    get_ayah_count,
    get_next_ayah,
    get_prev_ayah,
)
import user_data

# ========================
# 📝 LOGGING
# ========================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ========================
# 🌐 TRANSLATION
# ========================

yt = YandexFreeTranslate()


def translate_text(text: str, target_lang: str, source_lang: str = "auto") -> str:
    """Translate text using Yandex Free Translate (no API key required)."""
    if not text or not text.strip():
        return text
    try:
        max_chunk = 4000
        if len(text) <= max_chunk:
            return yt.translate(source_lang, target_lang, text)
        # Split long texts into chunks
        chunks = [text[i : i + max_chunk] for i in range(0, len(text), max_chunk)]
        return " ".join(yt.translate(source_lang, target_lang, c) for c in chunks)
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return f"[Ошибка перевода] {text[:200]}..."


# ========================
# 📡 QURAN API
# ========================


def fetch_ayah_text(surah_num: int, ayah_num: int, lang: str = "ru") -> dict | None:
    """Fetch Quran ayah text (Arabic + translation) from Al-Quran Cloud API."""
    try:
        edition = QURAN_EDITIONS.get(lang, DEFAULT_TRANSLATION)
        response = requests.get(
            f"{QURAN_API_BASE}/ayah/{surah_num}:{ayah_num}/editions/quran-unicode,{edition}",
            timeout=10,
        ).json()

        if response.get("code") == 200:
            return {
                "arabic": response["data"][0]["text"],
                "translation": response["data"][1]["text"],
                "surah_en": response["data"][0]["surah"]["englishName"],
                "surah_ar": response["data"][0]["surah"]["name"],
                "surah_num": surah_num,
                "ayah": ayah_num,
            }
    except Exception as e:
        logger.error(f"Quran API error: {e}")
    return None


def fetch_random_ayah(lang: str = "ru") -> dict | None:
    """Fetch a random ayah from any surah."""
    try:
        surah_num = random.randint(1, 114)
        total = get_ayah_count(surah_num)
        ayah_num = random.randint(1, total) if total > 0 else 1
        return fetch_ayah_text(surah_num, ayah_num, lang)
    except Exception as e:
        logger.error(f"Random ayah error: {e}")
        return None


# ========================
# 📚 HADITH API
# ========================


def fetch_random_hadith() -> dict:
    """Fetch a random Sahih Hadith from hadith-api."""
    try:
        response = requests.get(HADITH_API, timeout=10).json()
        if "data" in response:
            h = response["data"]
            return {
                "text": h.get("hadith_english", ""),
                "reference": (
                    f"Сахих аль-Бухари — Книга {h.get('bookNumber', '?')}, "
                    f"Хадис {h.get('hadithNumber', '?')}"
                ),
            }
    except Exception as e:
        logger.error(f"Hadith API error: {e}")

    # Fallback hadith
    return {
        "text": "Actions are judged by intentions, so each man will have what he intended.",
        "reference": "Сахих аль-Бухари и Сахих Муслим",
    }


# ========================
# 🎨 MESSAGE FORMATTING
# ========================

REFLECTIONS = [
    "💭 Размышление: Каждый аят — это послание, предназначенное именно для вас в этот момент.",
    "💭 Размышление: Коран — это зеркало души. Что вы видите в нём сегодня?",
    "💭 Размышление: Истинное знание приходит через размышление, а не просто чтение.",
    "💭 Размышление: Пусть каждое слово Аллаха станет светом на вашем пути.",
    "💭 Размышление: Терпение и благодарность — два крыла верующего.",
    "💭 Размышление: Каждый день — это возможность стать ближе к Аллаху.",
    "💭 Размышление: Мудрость Корана раскрывается тем, кто ищет её сердцем.",
    "💭 Размышление: В тишине размышления рождается истинное понимание.",
    "💭 Размышление: Аллах не обременяет душу сверх её возможностей.",
    "💭 Размышление: Пусть сегодняшний аят станет вашим проводником на весь день.",
]


def _streak_emoji(streak: int) -> str:
    if streak == 0:
        return ""
    fires = "🔥" * min(streak, 7)
    return f"{fires} Серия: {streak} дн."


def _build_ayah_keyboard(surah: int, ayah: int, current_lang: str) -> InlineKeyboardMarkup:
    """Build inline keyboard: navigation + language + bookmark."""
    p_surah, p_ayah = get_prev_ayah(surah, ayah)
    n_surah, n_ayah = get_next_ayah(surah, ayah)

    nav_row = [
        InlineKeyboardButton("⬅️ Пред.", callback_data=f"nav_{p_surah}_{p_ayah}_{current_lang}"),
        InlineKeyboardButton(f"📍 {surah}:{ayah}", callback_data="noop"),
        InlineKeyboardButton("След. ➡️", callback_data=f"nav_{n_surah}_{n_ayah}_{current_lang}"),
    ]

    lang_row = [
        InlineKeyboardButton(label, callback_data=f"lang_{code}_{surah}_{ayah}")
        for code, label in AVAILABLE_TRANSLATIONS.items()
        if code != current_lang
    ]

    action_row = [
        InlineKeyboardButton("🔖 Закладка", callback_data=f"bmark_{surah}_{ayah}"),
    ]

    return InlineKeyboardMarkup([nav_row, lang_row, action_row])


def _build_hadith_keyboard() -> InlineKeyboardMarkup:
    """Build inline keyboard for hadith messages."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Ещё хадис", callback_data="another_hadith"),
            InlineKeyboardButton("🌐 Перевести", callback_data="translate_hadith"),
        ]
    ])


def format_ayah_message(
    ayah_data: dict,
    qurtubi_tafsir: str,
    qushairi_tafsir: str,
    hadith: dict | None,
    lang: str,
    streak: int = 0,
) -> str:
    """Format a full ayah message with both tafsirs (HTML)."""
    surah_ar = get_surah_name(ayah_data["surah_num"])
    surah_en = ayah_data.get("surah_en", "")
    s = ayah_data["surah_num"]
    a = ayah_data["ayah"]

    # Translate tafsirs to the target language
    if lang == "ar":
        q_display = qurtubi_tafsir
        qs_display = translate_text(qushairi_tafsir, "ar", "en")
    elif lang == "ru":
        q_display = translate_text(qurtubi_tafsir, "ru", "ar")
        qs_display = translate_text(qushairi_tafsir, "ru", "en")
    elif lang == "en":
        q_display = translate_text(qurtubi_tafsir, "en", "ar")
        qs_display = qushairi_tafsir
    elif lang == "tr":
        q_display = translate_text(qurtubi_tafsir, "tr", "ar")
        qs_display = translate_text(qushairi_tafsir, "tr", "en")
    else:
        q_display = qurtubi_tafsir
        qs_display = qushairi_tafsir

    lang_flag = {"ru": "🇷🇺", "en": "🇬🇧", "tr": "🇹🇷"}.get(lang, "🌍")
    streak_line = f"\n{_streak_emoji(streak)}" if streak > 0 else ""

    msg = (
        f"╔══════════════════════════╗\n"
        f"   ✨ <b>КОРАН И ТАФСИР</b> ✨\n"
        f"╚══════════════════════════╝{streak_line}\n\n"
        f"🕌 <b>{surah_ar} ({surah_en})</b>\n"
        f"📍 Сура {s}, Аят {a}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📜 <b>Арабский текст:</b>\n"
        f"<i>{ayah_data['arabic']}</i>\n\n"
        f"{lang_flag} <b>Перевод:</b>\n"
        f"{ayah_data['translation']}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📚 <b>Тафсир аль-Куртуби:</b>\n"
        f"{q_display}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📖 <b>Тафсир аль-Кушайри:</b>\n"
        f"{qs_display}"
    )

    if hadith:
        h_text = hadith["text"]
        if lang == "ru":
            h_text = translate_text(h_text, "ru", "en")
        elif lang == "tr":
            h_text = translate_text(h_text, "tr", "en")

        msg += (
            f"\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📿 <b>Хадис дня:</b>\n"
            f"<i>{h_text}</i>\n\n"
            f"📖 <i>{hadith['reference']}</i>"
        )

    reflection = random.choice(REFLECTIONS)
    msg += (
        f"\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{reflection}\n\n"
        f"🤲 <i>Да благословит вас Аллах знанием и пониманием.</i>"
    )

    return msg


async def _safe_edit(query_or_msg, text: str, keyboard=None, parse_mode="HTML"):
    """Send or edit a message, truncating if it exceeds Telegram's limit."""
    try:
        if hasattr(query_or_msg, "edit_message_text"):
            await query_or_msg.edit_message_text(text, parse_mode=parse_mode, reply_markup=keyboard)
        else:
            await query_or_msg.edit_text(text, parse_mode=parse_mode, reply_markup=keyboard)
    except Exception as e:
        logger.warning(f"Message too long or edit error, truncating: {e}")
        short = text[:4000] + "\n\n⚠️ <i>Сообщение сокращено</i>"
        try:
            if hasattr(query_or_msg, "edit_message_text"):
                await query_or_msg.edit_message_text(short, parse_mode=parse_mode, reply_markup=keyboard)
            else:
                await query_or_msg.edit_text(short, parse_mode=parse_mode, reply_markup=keyboard)
        except Exception:
            pass


# ========================
# 🤖 BOT COMMANDS
# ========================


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start — Russian welcome with feature overview."""
    uid = update.effective_user.id
    streak_info = user_data.get_streak(uid)
    stats = user_data.get_reading_stats(uid)
    streak_display = _streak_emoji(streak_info["current"])

    msg = (
        f"✨ <b>Ас-саляму алейкум!</b> ✨\n\n"
        f"Добро пожаловать в <b>Коран и Тафсир Бот</b>! 🕌\n\n"
        f"{streak_display}\n\n"
        f"📅 <b>Возможности бота:</b>\n"
        f"  • Случайный аят с двумя тафсирами\n"
        f"  • Автоматический перевод (Яндекс)\n"
        f"  • 🇷🇺 Русский • 🇬🇧 English • 🇹🇷 Türkçe\n"
        f"  • ⬅️ ➡️ Листание аятов\n"
        f"  • 🔍 Поиск по тафсирам\n"
        f"  • 🔖 Закладки\n"
        f"  • 📊 Прогресс чтения\n"
        f"  • 🔥 Серия ежедневного чтения\n\n"
        f"📊 <b>Ваш прогресс:</b> {stats['total_read']}/{stats['total_ayahs']} аятов\n"
        f"{user_data.get_progress_bar(stats['percentage'])}\n\n"
        f"🎮 <b>Команды:</b>\n"
        f"/now — Получить аят прямо сейчас\n"
        f"/ayah 2:255 — Конкретный аят\n"
        f"/hadith — Случайный хадис\n"
        f"/search слово — Поиск в тафсирах\n"
        f"/bookmark 2:255 — Добавить закладку\n"
        f"/bookmarks — Мои закладки\n"
        f"/progress — Прогресс чтения\n"
        f"/times — Расписание\n"
        f"/lang — Сменить язык\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🤲 <i>Пусть этот бот приблизит вас к словам Аллаха.</i>"
    )

    await update.message.reply_text(msg, parse_mode="HTML")


async def now_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /now — send random ayah with tafsir immediately."""
    uid = update.effective_user.id
    lang = user_data.get_language(uid)
    streak = user_data.get_streak(uid)["current"]

    status_msg = await update.message.reply_text("📖 Загружаю аят для вас... ✨")

    ayah_data = fetch_random_ayah(lang)
    if not ayah_data:
        await status_msg.edit_text("❌ Ошибка загрузки. Попробуйте ещё раз.")
        return

    s, a = ayah_data["surah_num"], ayah_data["ayah"]
    qurtubi = get_tafsir_for_ayah(s, a, "qurtubi")
    qushairi = get_tafsir_for_ayah(s, a, "qushairi")
    hadith = fetch_random_hadith()

    user_data.mark_ayah_read(uid, s, a)

    msg = format_ayah_message(ayah_data, qurtubi, qushairi, hadith, lang, streak)
    keyboard = _build_ayah_keyboard(s, a, lang)
    await _safe_edit(status_msg, msg, keyboard)


async def ayah_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ayah surah:ayah — fetch a specific ayah."""
    uid = update.effective_user.id
    lang = user_data.get_language(uid)
    streak = user_data.get_streak(uid)["current"]

    if not context.args:
        await update.message.reply_text(
            "📌 <b>Использование:</b> <code>/ayah 2:255</code>\n"
            "Формат: сура:аят (например, 1:1, 36:1, 112:1)",
            parse_mode="HTML",
        )
        return

    try:
        parts = context.args[0].split(":")
        s, a = int(parts[0]), int(parts[1])
        if not (1 <= s <= 114) or not (1 <= a <= get_ayah_count(s)):
            raise ValueError
    except (ValueError, IndexError):
        await update.message.reply_text(
            "❌ Неверный формат. Используйте: <code>/ayah 2:255</code>", parse_mode="HTML"
        )
        return

    status_msg = await update.message.reply_text("📖 Загружаю аят... ✨")

    ayah_data = fetch_ayah_text(s, a, lang)
    if not ayah_data:
        await status_msg.edit_text("❌ Ошибка загрузки аята.")
        return

    qurtubi = get_tafsir_for_ayah(s, a, "qurtubi")
    qushairi = get_tafsir_for_ayah(s, a, "qushairi")
    user_data.mark_ayah_read(uid, s, a)

    msg = format_ayah_message(ayah_data, qurtubi, qushairi, None, lang, streak)
    keyboard = _build_ayah_keyboard(s, a, lang)
    await _safe_edit(status_msg, msg, keyboard)


async def hadith_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /hadith — send a random Sahih hadith."""
    uid = update.effective_user.id
    lang = user_data.get_language(uid)

    hadith = fetch_random_hadith()
    h_text = hadith["text"]

    if lang == "ru":
        h_text = translate_text(h_text, "ru", "en")
    elif lang == "tr":
        h_text = translate_text(h_text, "tr", "en")

    msg = (
        f"📿 <b>Хадис</b>\n\n"
        f"<i>{h_text}</i>\n\n"
        f"📖 <i>{hadith['reference']}</i>"
    )

    await update.message.reply_text(msg, parse_mode="HTML", reply_markup=_build_hadith_keyboard())


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /search keyword — search tafsirs."""
    if not context.args:
        await update.message.reply_text(
            "🔍 <b>Использование:</b> <code>/search mercy</code>\n"
            "Поиск слова в тафсире аль-Кушайри (на английском)",
            parse_mode="HTML",
        )
        return

    keyword = " ".join(context.args)
    await update.message.reply_text(f"🔍 Ищу «{keyword}» в тафсирах...")

    results = search_tafsir(keyword, "qushairi", max_results=8)

    if not results:
        await update.message.reply_text(
            f"😔 По запросу «{keyword}» ничего не найдено.\n"
            "Попробуйте другое слово (поиск на английском)."
        )
        return

    msg = f"🔍 <b>Результаты поиска: «{keyword}»</b>\nНайдено: {len(results)} совпадений\n\n"
    for i, r in enumerate(results, 1):
        snippet = r["snippet"].replace("<", "&lt;").replace(">", "&gt;")
        msg += f"<b>{i}. {r['surah_name']} — {r['surah']}:{r['ayah']}</b>\n<i>{snippet}</i>\n\n"

    msg += "📌 Используйте <code>/ayah сура:аят</code> для чтения полного тафсира."

    try:
        await update.message.reply_text(msg, parse_mode="HTML")
    except Exception:
        await update.message.reply_text(msg[:4000], parse_mode="HTML")


async def bookmark_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /bookmark surah:ayah — add bookmark."""
    uid = update.effective_user.id

    if not context.args:
        await update.message.reply_text(
            "🔖 <b>Использование:</b> <code>/bookmark 2:255</code>", parse_mode="HTML"
        )
        return

    try:
        parts = context.args[0].split(":")
        s, a = int(parts[0]), int(parts[1])
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Формат: <code>/bookmark 2:255</code>", parse_mode="HTML")
        return

    if user_data.add_bookmark(uid, s, a):
        name = get_surah_name(s)
        await update.message.reply_text(
            f"✅ <b>Закладка добавлена!</b>\n🔖 {name} — {s}:{a}", parse_mode="HTML"
        )
    else:
        await update.message.reply_text("📌 Этот аят уже в закладках!")


async def bookmarks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /bookmarks — list all bookmarks."""
    uid = update.effective_user.id
    bookmarks = user_data.get_bookmarks(uid)

    if not bookmarks:
        await update.message.reply_text(
            "📌 У вас пока нет закладок.\n"
            "Используйте <code>/bookmark 2:255</code> или кнопку 🔖",
            parse_mode="HTML",
        )
        return

    msg = "🔖 <b>Ваши закладки:</b>\n\n"
    for i, ref in enumerate(bookmarks, 1):
        s, a = ref.split(":")
        msg += f"  {i}. {get_surah_name(int(s))} — <code>{ref}</code>\n"

    msg += f"\n📊 Всего: {len(bookmarks)} закладок\n"
    msg += "📌 Нажмите на код аята и используйте <code>/ayah</code> для чтения."
    await update.message.reply_text(msg, parse_mode="HTML")


async def progress_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /progress — show reading progress and streak."""
    uid = update.effective_user.id
    stats = user_data.get_reading_stats(uid)
    streak_info = user_data.get_streak(uid)
    bar = user_data.get_progress_bar(stats["percentage"])

    active_today = "✅ Вы уже читали сегодня!" if streak_info["active_today"] else "⏳ Используйте /now!"

    msg = (
        f"📊 <b>Прогресс чтения Корана</b>\n\n"
        f"{bar}\n\n"
        f"📖 Прочитано аятов: <b>{stats['total_read']}</b> из <b>{stats['total_ayahs']}</b>\n"
        f"📈 Процент: <b>{stats['percentage']}%</b>\n\n"
        f"🔥 <b>Серия чтения:</b>\n"
        f"  Текущая: <b>{streak_info['current']}</b> дн.\n"
        f"  Лучшая: <b>{streak_info['max']}</b> дн.\n"
        f"  {_streak_emoji(streak_info['current'])}\n\n"
        f"{active_today}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💡 <i>Читайте каждый день, чтобы не прерывать серию!</i>"
    )

    await update.message.reply_text(msg, parse_mode="HTML")


async def times_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /times — show daily message schedule."""
    times_list = "\n".join([f"  🕐 {t}" for t in SCHEDULE_TIMES])
    interval = 24 * 60 // len(SCHEDULE_TIMES)

    msg = (
        f"⏰ <b>Расписание ежедневных сообщений</b>\n\n"
        f"{times_list}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 <b>Всего:</b> {len(SCHEDULE_TIMES)} сообщений в день\n"
        f"⏱️ <b>Интервал:</b> ~{interval} мин.\n\n"
        f"Используйте /now для немедленного чтения!"
    )

    await update.message.reply_text(msg, parse_mode="HTML")


async def lang_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /lang — show language selection buttons."""
    uid = update.effective_user.id
    current = user_data.get_language(uid)

    keyboard = [
        [InlineKeyboardButton(
            f"{label}{' ✅' if code == current else ''}",
            callback_data=f"setlang_{code}",
        )]
        for code, label in AVAILABLE_TRANSLATIONS.items()
    ]

    await update.message.reply_text(
        f"🌍 <b>Выберите язык:</b>\n\nТекущий: {AVAILABLE_TRANSLATIONS.get(current, current)}",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ========================
# 🔄 CALLBACK HANDLERS
# ========================


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route all inline-button callback queries."""
    query = update.callback_query
    data = query.data

    if data == "noop":
        await query.answer()
        return

    if data.startswith("nav_"):
        await _cb_navigation(query)
    elif data.startswith("lang_"):
        await _cb_language_switch(query)
    elif data.startswith("setlang_"):
        await _cb_set_language(query)
    elif data.startswith("bmark_"):
        await _cb_bookmark(query)
    elif data == "another_hadith":
        await _cb_another_hadith(query)
    elif data == "translate_hadith":
        await _cb_translate_hadith(query)
    else:
        await query.answer("❓ Неизвестная команда")


async def _cb_navigation(query):
    """Handle ⬅️ Previous | Next ➡️ navigation."""
    await query.answer("📖 Загружаю...")

    try:
        parts = query.data.split("_")
        surah, ayah, lang = int(parts[1]), int(parts[2]), parts[3] if len(parts) > 3 else "ru"
    except (ValueError, IndexError):
        await query.answer("❌ Ошибка навигации")
        return

    uid = query.from_user.id
    streak = user_data.get_streak(uid)["current"]

    ayah_data = fetch_ayah_text(surah, ayah, lang)
    if not ayah_data:
        await query.answer("❌ Ошибка загрузки")
        return

    qurtubi = get_tafsir_for_ayah(surah, ayah, "qurtubi")
    qushairi = get_tafsir_for_ayah(surah, ayah, "qushairi")
    user_data.mark_ayah_read(uid, surah, ayah)

    msg = format_ayah_message(ayah_data, qurtubi, qushairi, None, lang, streak)
    keyboard = _build_ayah_keyboard(surah, ayah, lang)
    await _safe_edit(query, msg, keyboard)


async def _cb_language_switch(query):
    """Handle language switch button on an ayah message."""
    await query.answer("🌐 Переключаю язык...")

    try:
        parts = query.data.split("_")
        target_lang, surah, ayah = parts[1], int(parts[2]), int(parts[3])
    except (ValueError, IndexError):
        await query.answer("❌ Ошибка")
        return

    uid = query.from_user.id
    streak = user_data.get_streak(uid)["current"]

    ayah_data = fetch_ayah_text(surah, ayah, target_lang)
    if not ayah_data:
        await query.answer("❌ Ошибка загрузки")
        return

    qurtubi = get_tafsir_for_ayah(surah, ayah, "qurtubi")
    qushairi = get_tafsir_for_ayah(surah, ayah, "qushairi")

    msg = format_ayah_message(ayah_data, qurtubi, qushairi, None, target_lang, streak)
    keyboard = _build_ayah_keyboard(surah, ayah, target_lang)
    await _safe_edit(query, msg, keyboard)


async def _cb_set_language(query):
    """Handle global language preference change from /lang menu."""
    lang = query.data.replace("setlang_", "")
    uid = query.from_user.id
    user_data.set_language(uid, lang)

    label = AVAILABLE_TRANSLATIONS.get(lang, lang)
    await query.answer(f"✅ Язык: {label}")

    keyboard = [
        [InlineKeyboardButton(
            f"{lb}{' ✅' if code == lang else ''}",
            callback_data=f"setlang_{code}",
        )]
        for code, lb in AVAILABLE_TRANSLATIONS.items()
    ]

    await query.edit_message_text(
        f"🌍 <b>Язык установлен:</b> {label}\n\n"
        "Все последующие сообщения будут на выбранном языке.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def _cb_bookmark(query):
    """Handle bookmark button press on ayah message."""
    try:
        parts = query.data.split("_")
        surah, ayah = int(parts[1]), int(parts[2])
    except (ValueError, IndexError):
        await query.answer("❌ Ошибка")
        return

    uid = query.from_user.id
    if user_data.add_bookmark(uid, surah, ayah):
        name = get_surah_name(surah)
        await query.answer(f"✅ Закладка: {name} {surah}:{ayah}")
    else:
        await query.answer("📌 Уже в закладках!")


async def _cb_another_hadith(query):
    """Handle 'Another hadith' button."""
    await query.answer("📿 Загружаю...")

    uid = query.from_user.id
    lang = user_data.get_language(uid)
    hadith = fetch_random_hadith()
    h_text = hadith["text"]

    if lang == "ru":
        h_text = translate_text(h_text, "ru", "en")
    elif lang == "tr":
        h_text = translate_text(h_text, "tr", "en")

    msg = f"📿 <b>Хадис</b>\n\n<i>{h_text}</i>\n\n📖 <i>{hadith['reference']}</i>"
    await _safe_edit(query, msg, _build_hadith_keyboard())


async def _cb_translate_hadith(query):
    """Translate the current hadith message into EN / TR / RU."""
    await query.answer("🌐 Перевожу...")

    original_text = query.message.text or ""
    if not original_text:
        await query.answer("❌ Текст недоступен")
        return

    en = translate_text(original_text, "en", "auto")
    tr = translate_text(original_text, "tr", "auto")

    msg = f"🇬🇧 <b>English:</b>\n{en}\n\n🇹🇷 <b>Türkçe:</b>\n{tr}"
    try:
        await query.message.reply_text(msg, parse_mode="HTML")
    except Exception:
        await query.message.reply_text(msg[:4000], parse_mode="HTML")


# ========================
# ⏰ SCHEDULED MESSAGES
# ========================


async def send_scheduled_message(app):
    """Send a scheduled ayah + tafsir + hadith to CHAT_ID."""
    try:
        logger.info("📤 Sending scheduled message...")

        ayah_data = fetch_random_ayah("ru")
        if not ayah_data:
            logger.error("Failed to fetch ayah for scheduled message")
            return

        s, a = ayah_data["surah_num"], ayah_data["ayah"]
        qurtubi = get_tafsir_for_ayah(s, a, "qurtubi")
        qushairi = get_tafsir_for_ayah(s, a, "qushairi")
        hadith = fetch_random_hadith()

        msg = format_ayah_message(ayah_data, qurtubi, qushairi, hadith, "ru", 0)
        keyboard = _build_ayah_keyboard(s, a, "ru")

        await app.bot.send_message(
            chat_id=CHAT_ID,
            text=msg[:4096],
            parse_mode="HTML",
            reply_markup=keyboard,
        )
        logger.info("✅ Scheduled message sent")
    except Exception as e:
        logger.error(f"Scheduled message error: {e}")


# ========================
# 🚀 MAIN
# ========================


async def main():
    """Initialize and run the bot."""
    logger.info("🤖 Запуск Quran & Tafsir Bot...")

    app = Application.builder().token(BOT_TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("now", now_command))
    app.add_handler(CommandHandler("ayah", ayah_command))
    app.add_handler(CommandHandler("hadith", hadith_command))
    app.add_handler(CommandHandler("search", search_command))
    app.add_handler(CommandHandler("bookmark", bookmark_command))
    app.add_handler(CommandHandler("bookmarks", bookmarks_command))
    app.add_handler(CommandHandler("progress", progress_command))
    app.add_handler(CommandHandler("times", times_command))
    app.add_handler(CommandHandler("lang", lang_command))

    # Inline button handler
    app.add_handler(CallbackQueryHandler(handle_callback))

    # APScheduler for daily messages
    scheduler = AsyncIOScheduler()
    for time_str in SCHEDULE_TIMES:
        hour, minute = map(int, time_str.split(":"))
        scheduler.add_job(send_scheduled_message, "cron", hour=hour, minute=minute, args=[app])
        logger.info(f"📅 Запланировано: {time_str}")

    scheduler.start()

    logger.info("✅ Бот запущен!")
    logger.info(f"📅 {len(SCHEDULE_TIMES)} сообщений в день")
    logger.info(f"💬 Chat ID: {CHAT_ID}")
    logger.info("Нажмите Ctrl+C для остановки")

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("🛑 Остановка бота...")
        scheduler.shutdown()
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен")
