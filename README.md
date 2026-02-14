# 🕌 Quran & Tafsir Telegram Bot

**All-in-one Telegram bot with embedded web server** for delivering daily Quran ayahs with full tafsir commentary via Telegram Mini Apps.

## Features

- 📖 **Telegram Mini App** — View full tafsir (al-Qurtubi + al-Qushairi) without 4096-char message limits
- ⏰ **Personal Reminders** — Set daily reminders for any ayah at any time
- 📅 **Auto-scheduled Messages** — 10 daily ayah messages automatically
- 🌍 **Multi-language** — Russian, English, Turkish (Yandex translation)
- 🔖 **Bookmarks & Progress** — Track your reading journey
- 🔥 **Streaks** — Daily reading streak tracking
- ⬅️➡️ **Navigation** — Browse ayahs with inline buttons

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure (Optional)

Set environment variables for production:

```bash
export BOT_TOKEN="your-telegram-bot-token"
export CHAT_ID="your-telegram-chat-id"
export WEBAPP_URL="https://your-domain.com"  # Required for Mini Apps
```

Or edit `config.py` directly.

### 3. Run Everything

```bash
python main.py
```

This single command starts:
- ✅ Telegram bot (polling)
- ✅ Flask web server (port 5000, serves Mini App)
- ✅ Scheduler (auto-messages + reminders)

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message with feature overview |
| `/now` | Get a random ayah right now |
| `/ayah 2:255` | Get a specific ayah (e.g., Ayat al-Kursi) |
| `/hadith` | Random Sahih Bukhari hadith |
| `/remind 08:30` | Daily reminder at 08:30 (random ayah) |
| `/remind 08:30 2:255` | Daily reminder for specific ayah |
| `/reminders` | List all your reminders |
| `/delremind 1` | Delete reminder #1 |
| `/search mercy` | Search tafsir for keywords |
| `/bookmark 2:255` | Add ayah to bookmarks |
| `/bookmarks` | List your bookmarks |
| `/progress` | View reading stats & streak |
| `/times` | Show auto-schedule times |
| `/lang` | Change language (RU/EN/TR) |

## Mini App (Web Tafsir)

Every ayah message has a **"📖 Читать полный Тафсир"** button that opens a beautiful mobile-optimized web view inside Telegram showing:

- Full Arabic ayah text with proper typography
- Translation in your language
- Complete Tafsir al-Qurtubi (classical Arabic commentary)
- Complete Tafsir al-Qushairi (English spiritual commentary)
- Collapsible sections, language switcher, ayah navigation

**No 4096-character message limit!**

## Production Deployment

Telegram Mini Apps require HTTPS. Options:

### Option A: ngrok (for testing)

```bash
ngrok http 5000
# Copy the https URL
export WEBAPP_URL=https://xxxx.ngrok-free.app
python main.py
```

### Option B: Deploy to Render/Railway

1. Push code to GitHub
2. Deploy to Render or Railway
3. Set `WEBAPP_URL` to your deployment URL (e.g., `https://your-app.onrender.com`)

## File Structure

```
Barkhudarov_Bot/
├── main.py                    # Bot + Flask server + scheduler (all-in-one)
├── config.py                  # Settings & environment variables
├── tafsir_loader.py           # Local tafsir data loader
├── user_data.py               # User data (bookmarks, reminders, progress)
├── requirements.txt           # Python dependencies
├── webapp/
│   └── index.html            # Telegram Mini App (single-page app)
├── ar-tafseer-al-qurtubi/    # Local tafsir data (114 surah folders)
└── en-al-qushairi-tafsir/    # Local tafsir data (114 surah folders)
```

## Data Persistence

All user data is stored in `user_data.json`:
- Bookmarks
- Reading progress & streaks
- Language preferences
- Personal reminders

## API Endpoints

The embedded Flask server provides:

- `GET /webapp` — Serves the Mini App HTML
- `GET /api/tafsir?surah=1&ayah=1&lang=ru` — Full tafsir JSON
- `GET /api/surah-list` — List all 114 surahs
- `GET /api/health` — Health check

## Tech Stack

- **python-telegram-bot** 20.7 — Telegram Bot API
- **Flask** 3.1.0 — Web server for Mini App
- **APScheduler** 3.10.4 — Scheduled messages & reminders
- **yandexfreetranslate** — Free translation (no API key)
- Local JSON tafsir data (no external APIs)

## License

Personal project for Quran study and reflection.

## Credits

- Tafsir al-Qurtubi (Arabic classical commentary)
- Tafsir al-Qushairi (English spiritual commentary)
- Al-Quran Cloud API for Quran text
- Random Hadith API for Sahih Bukhari hadiths
