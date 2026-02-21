# 🕌 Hadith Telegram Bot (Personal)

Telegram bot for delivering authentic Hadith (Sahih Bukhari) with **daily delivery**, **favorites**, and **category-based fetching**.

---

## Features

### 1) Daily Hadith at a fixed time (sequential, not random)
- The bot sends **one hadith daily** at your chosen time (e.g., 08:30)
- It uses a **sequential index** so you don’t keep repeating the same hadith

### 2) Favorites ⭐
- Save a hadith you like with `/fav`
- Browse your saved list with `/favorites`

### 3) Category-based Hadith
- Request hadith by category (example: patience, prayer, character)
- Example: `/hadith sabr`

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure

Set environment variables:

```bash
export BOT_TOKEN="your-telegram-bot-token"
export CHAT_ID="your-telegram-chat-id"
```

Or edit `config.py` directly.

### 3. Run the Bot

```bash
python main.py
```

This starts:
- ✅ Telegram bot (polling)
- ✅ Scheduler (daily hadith + reminders)

---

## Commands

| Command | Description |
|--------|-------------|
| `/start` | Welcome message |
| `/hadith` | Get a random hadith (fallback mode) |
| `/hadith <category>` | Get a hadith by category (e.g., `/hadith sabr`) |
| `/daily <HH:MM>` | Set **daily hadith time** (sequential delivery) |
| `/dailyoff` | Disable daily hadith |
| `/fav` | Save the **last hadith** as favorite ⭐ |
| `/favorites` | List favorites |
| `/unfav <id>` | Remove a favorite by id |
| `/remind <HH:MM>` | Daily reminder (separate from `/daily`) |
| `/reminders` | List reminders |
| `/delremind <id>` | Delete reminder #id |
| `/lang` | Change language (RU/EN/TR) |

---

## File Structure (Hadith-only)

```
Barkhudarov_Bot/
├── main.py              # Telegram bot + scheduler
├── config.py            # Settings & environment variables
├── user_data.py         # User storage (daily time, favorites, prefs)
├── requirements.txt     # Python dependencies
├── user_data.json       # Runtime storage (created automatically)
```

---

## Data Persistence

User data is stored in `user_data.json`, including:
- Daily hadith time (HH:MM)
- Daily sequential index (which hadith was last sent)
- Favorites list
- Language preference
- Reminders (if you keep them)

---



## Tech Stack

- **python-telegram-bot** — Telegram Bot API
- **APScheduler** — Scheduled jobs (daily hadith + reminders)
- Hadith source:
  - Either an API (Random Hadith / Bukhari source) **or**
  - A local dataset (recommended later for reliability)

---

## License

Personal project for Hadith study and reflection.
