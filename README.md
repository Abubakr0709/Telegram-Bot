# ?? Hadith Telegram Bot

Telegram bot for authentic Hadith (Sahih Bukhari) with a clean Telegram UX, image cards, favorites, and guided daily notifications.

---

## Features

### 1) Guided interface (button-first)
- `/start` shows a clean menu:
  - **Get Hadith**
  - **Notifications**
  - **Favorites**
  - **Language**
- No need to remember scheduler commands.

### 2) Hadith image cards
- Every hadith delivery is sent as a generated quote-card image.
- Works for:
  - Manual `/hadith`
  - Callback "Another hadith"
  - Scheduled daily hadith
- If image rendering fails, bot automatically falls back to text.

### 3) Daily hadith notifications (single schedule)
- One daily time per user (HH:MM), managed via **Notifications** menu.
- Sequential hadith index is used for daily delivery.
- You can set time or turn notifications off from buttons.

### 4) Favorites
- Save last hadith with `/fav` or inline button.
- View with `/favorites`.
- Remove with `/unfav <id>`.

### 5) Multi-language
- RU / EN / TR UI support.
- Language can be changed from `/lang` or menu button.

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure

Set environment variable:

```bash
export BOT_TOKEN="your-telegram-bot-token"
```

Or edit `config.py`.

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
| `/hadith` | Random hadith card |
| `/hadith <keyword>` | Search hadith by keyword |
| `/favorites` | List favorites |
| `/unfav <id>` | Remove favorite by id |
| `/lang` | Change language |

You can still save quickly using inline **Save to favourites** buttons on hadith cards. Legacy scheduler/reminder commands are deprecated and redirect users to the **Notifications** button flow.

---

## Project Structure

```
Barkhudarov_Bot/
+-- main.py
+-- hadith_card.py
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
- `Pillow`

---

## License

Personal project for Hadith study and reflection.
