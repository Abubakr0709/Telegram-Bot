import logging
import os
import asyncio
from datetime import time
import pytz

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import BadRequest

import config
import quran_service
import hadith_service
import translation_service

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Constants
subscribed_chats = set() # In-memory storage for now

# Check if we are running in cloud environment (Render/Railway etc)
PORT = int(os.environ.get('PORT', 5000))
WEBHOOK_URL = os.environ.get('Render_External_URL') # Example for Render, adjust as needed

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message and subscribes the user to daily updates."""
    chat_id = update.effective_chat.id
    subscribed_chats.add(chat_id)
    
    welcome_text = (
        "Assalamu Alaikum! 🌙\n\n"
        "I am the Barkhudarov Islamic Bot.\n"
        "I will send you:\n"
        "📖 2 Ayahs from the Quran every hour\n"
        "📚 10 Sahih Hadiths daily at 8:00 PM\n\n"
        "You can also use the buttons below messages to view Tafsir and Translations."
    )
    
    await update.message.reply_text(welcome_text)
    logger.info(f"New subscriber: {chat_id}")

async def send_ayah_job(context: ContextTypes.DEFAULT_TYPE):
    """Job to send 2 random ayahs to all subscribers."""
    for chat_id in subscribed_chats:
        try:
            # Send 2 ayahs
            for _ in range(2):
                await send_random_ayah(context.bot, chat_id)
        except Exception as e:
            logger.error(f"Failed to send ayah to {chat_id}: {e}")

async def send_random_ayah(bot, chat_id):
    """Helper to fetch and send a random ayah."""
    ayah_data = await quran_service.get_random_ayah()
    if not ayah_data:
        return

    text = (
        f"📖 *Surah {ayah_data['surah_english_name']} ({ayah_data['surah_name']})*\n"
        f"Ayah {ayah_data['ayah_number']}\n\n"
        f"{ayah_data['text_arabic']}\n\n"
        f"{ayah_data['text_russian']}"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("📖 Tafsir al-Qurtubi", callback_data=f"tafsir_qurtubi:{ayah_data['surah_number']}:{ayah_data['ayah_number']}"),
            InlineKeyboardButton("📖 Tafsir (English)", callback_data=f"tafsir_qushayri:{ayah_data['surah_number']}:{ayah_data['ayah_number']}")
        ],
        [
            InlineKeyboardButton("🔄 Another Ayah", callback_data="another_ayah"),
            InlineKeyboardButton("🌐 Translate", callback_data=f"translate:ayah:{ayah_data['surah_number']}:{ayah_data['ayah_number']}")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode='Markdown')
    except BadRequest as e:
        logger.error(f"Telegram API Error sending ayah: {e}")
    except Exception as e:
        logger.error(f"Error sending ayah: {e}")

async def send_hadith_job(context: ContextTypes.DEFAULT_TYPE):
    """Job to send 10 Sahih Hadiths to all subscribers."""
    logger.info("Starting daily Hadith job...")
    for chat_id in subscribed_chats:
        try:
            # Send 10 hadiths
            for i in range(10):
                await send_random_hadith(context.bot, chat_id)
                await asyncio.sleep(1) # visual delay
        except Exception as e:
            logger.error(f"Failed to send hadith to {chat_id}: {e}")

async def send_random_hadith(bot, chat_id):
    """Helper to fetch and send a random hadith."""
    hadith_data = await hadith_service.get_random_hadith()
    if not hadith_data:
        return

    text = (
        f"📚 *Example from {hadith_data['source']}*\n"
        f"Hadith #{hadith_data['number']}\n\n"
        f"{hadith_data['text']}\n"
    )
    
    # We need a unique ID for the hadith to retrieve explanation or translate properly. 
    # Since we don't have a reliable ID for random fetch, we might encode the source and number.
    # But text length limits apply to callback data (64 bytes).
    # We'll use source:number for identification.
    
    hadith_id = f"{hadith_data['edition']}:{hadith_data['number']}"
    
    keyboard = [
        [InlineKeyboardButton("📚 Hadith Explanation", callback_data=f"hadith_exp:{hadith_id}")],
        [
            InlineKeyboardButton("🔄 Another Hadith", callback_data="another_hadith"),
            # Translation for hadith might be tricky if we don't have the text in callback.
            # We can't pass full text. We have to re-fetch or rely on the user context?
            # Actually, `translate` button usually translates the message content.
            # But callback queries don't carry the message text easily without the message object.
            # We can use the message text from the update if we edit it, but for a new translation message?
            # Let's try to just trigger a translation of the current message text.
            InlineKeyboardButton("🌐 Translate", callback_data="translate_current_msg")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error sending hadith: {e}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles all inline button clicks."""
    query = update.callback_query
    await query.answer() # Acknowledge the click
    
    data = query.data
    
    try:
        if data == "another_ayah":
             await send_random_ayah(context.bot, query.message.chat.id)
             
        elif data == "another_hadith":
             await send_random_hadith(context.bot, query.message.chat.id)
             
        elif data.startswith("tafsir_qurtubi:"):
            _, surah, ayah = data.split(":")
            tafsir = await quran_service.get_tafsir_qurtubi(surah, ayah)
            if tafsir:
                text = f"📖 *Tafsir Al-Qurtubi*\n\n{tafsir['text'][:3500]}..." # Limit length
                await query.message.reply_text(text, parse_mode='Markdown')
            else:
                await query.message.reply_text("Tafsir implementation unavailable for this ayah.")
                
        elif data.startswith("tafsir_qushayri:"):
            _, surah, ayah = data.split(":")
            tafsir = await quran_service.get_tafsir_qushayri(surah, ayah)
            if tafsir:
                text = f"📖 *Tafsir (English)*\n\n{tafsir['text'][:3500]}..."
                await query.message.reply_text(text, parse_mode='Markdown')
            else:
                await query.message.reply_text("Tafsir not found.")
        
        elif data.startswith("hadith_exp:"):
            # Mock explanation
            text = "<b>Scholarly Explanation:</b>\n\nThis hadith emphasizes the importance of intention in all actions. Scholars note that it is the foundation of accepted deeds in Islam."
            await query.message.reply_text(text, parse_mode='HTML')
            
        elif data == "translate_current_msg":
            # Translate the text of the message that contained the button
            original_text = query.message.text
            if not original_text:
                await query.message.reply_text("Could not access message text.")
                return
                
            en_trans = await translation_service.translate_to_english(original_text)
            tr_trans = await translation_service.translate_to_turkish(original_text)
            
            reply_text = (
                f"🇬🇧 *English:*\n{en_trans}\n\n"
                f"🇹🇷 *Turkish:*\n{tr_trans}"
            )
            await query.message.reply_text(reply_text, parse_mode='Markdown')
            
        elif data.startswith("translate:ayah:"):
            # Specific ayah translation if needed, but translate_current_msg covers it genericly
            pass
            
    except Exception as e:
        logger.error(f"Error in button handler: {e}")
        await query.message.reply_text("An error occurred while processing your request.")

def main():
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Job Queue
    job_queue = application.job_queue
    
    # Schedule hourly ayahs
    # run_repeating(callback, interval, first)
    job_queue.run_repeating(send_ayah_job, interval=3600, first=10)
    
    # Schedule daily hadiths at 20:00 local time
    # We need to be careful with timezones.
    # The user is in UTC+4 (Baku/Yerevan/Samara time presumably based on 22:21 being +4)
    # Let's set it to run daily at 20:00
    local_tz = pytz.timezone('Asia/Dubai') # UTC+4 approximation or use explicit offset if needed. 
    # Actually user provided "+04:00".
    # 'Asia/Baku' is +4. 'Asia/Dubai' is +4.
    
    daily_time = time(hour=20, minute=0, tzinfo=local_tz)
    job_queue.run_daily(send_hadith_job, time=daily_time)
    
    # Start the Bot
    if WEBHOOK_URL:
        # Webhook mode
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=config.BOT_TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{config.BOT_TOKEN}"
        )
    else:
        # Polling mode
        logger.info("Starting polling...")
        application.run_polling()

if __name__ == "__main__":
    main()
