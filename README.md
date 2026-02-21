# 🕌 Hadith Telegram Bot

Telegram bot for authentic Hadith (Sahih Bukhari) with **beautiful Islamic image cards**, favorites, daily notifications, and multi-language support (RU/EN/TR).

---

## ✨ Features

### 1) Beautiful Islamic Image Cards
- Every hadith is delivered as a **high-quality graphic card** with:
  - Authentic Islamic imagery (mosques, Quran, calligraphy, Kaaba, etc.)
  - Hadith text elegantly overlaid with perfect readability
  - 1080x1350px resolution optimized for mobile screens
- Backgrounds sourced from:
  - **Unsplash API** (optional, for diverse fresh images)
  - **Curated cache** (pre-downloaded Islamic photos, works offline)
  - **Islamic gradient** (elegant fallback if images unavailable)

### 2) Guided Interface (Button-First)
- `/start` shows a clean menu:
  - **📿 Get Hadith**
  - **⏰ Notifications**
  - **⭐ Favorites**
  - **🌍 Language**
- No need to remember complex commands

### 3) Daily Hadith Notifications
- Set a single daily time (HH:MM) per user
- Sequential hadith delivery (no repeats)
- Managed via interactive buttons
- Enable/disable easily from the Notifications menu

### 4) Favorites ⭐
- Save hadiths with `/fav` or inline button
- View collection with `/favorites`
- Remove with `/unfav <id>`

### 5) Multi-Language 🌍
- Full UI support: Russian, English, Turkish
- Switch language anytime via `/lang` or menu

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. (Optional) Download Islamic Image Cache

Pre-download curated Islamic backgrounds for offline use:

```bash
python download_islamic_images.py
```

This creates a `.image_cache/` folder with high-quality Islamic images.

### 3. Configure

Set environment variables:

```bash
export BOT_TOKEN="your-telegram-bot-token"
export UNSPLASH_ACCESS_KEY="your-unsplash-api-key"  # Optional
```

Or edit `config.py`.

> **Note:** Unsplash API key is optional. The bot works perfectly with cached images or gradient fallback.

### 3. Run

```bash
python main.py
```

Starts:
- Telegram bot polling
- APScheduler for daily jobs

---

## Bot Commands (visible menu)

| Command | Description |
|--------|-------------|
| `/start` | Welcome + main menu |
| `/hadith` | Random hadith |
| `/hadith <keyword>` | Search hadith by keyword |
| `/favorites` | List favorites |
| `/unfav <id>` | Remove favorite by id |
| `/lang` | Change language |

You can still save quickly using inline **Save to favourites** buttons on hadith messages. Legacy scheduler/reminder commands are deprecated and redirect users to the **Notifications** button flow.

---

## Project Structure

```
Barkhudarov_Bot/
+-- main.py
+-- islamic_images.py
+-- user_data.py
+-- config.py
+-- requirements.txt
+-- user_data.json
```

---

## Data Persistence

`user_data.json` stores:
- `daily_time`
- `daily_index`
- `favorites`
- `language`
- `last_hadith`

---

## Tech Stack

- `python-telegram-bot`
- `APScheduler`
- `requests`
- `deep-translator`
- `Pexels API`

---

## License

Personal project for Hadith study and reflection.
