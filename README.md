# 🕌 Hadith Telegram Bot

Telegram bot for authentic Hadith (Sahih Bukhari) with **beautiful Islamic image cards**, favorites, daily notifications, and multi-language support (RU/EN/TR).

---

## Recent Updates

- Removed raw HTML tags from image captions in Telegram photo messages (no more `<b>...</b>` under generated pictures).
- Improved Railway font loading for card rendering (checks bundled `fonts/NotoSans-Regular.ttf` and Linux font paths before fallback).
- Added runtime font bootstrap on Railway: if `fonts/NotoSans-Regular.ttf` is missing, the bot downloads Noto Sans automatically for proper Unicode rendering.
- Removed card byte caching and randomized fallback gradient palettes so generated cards do not keep the same static look.
- Conservative maintenance cleanup:
  - removed `bulk_downloader.py` (unused script with hardcoded API key)
  - removed runtime artifact folder `__pycache__/`
  - extended `.gitignore` for `.venv-1/`, `.venv-2/`, and `.image_cache/`
  - removed dead code (`CHAT_ID`, unused formatter helper, unused legacy gradient helper)

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

If card text looks like a thin white line in production, add a Unicode font file at `fonts/NotoSans-Regular.ttf` in this repo and redeploy.

### 3. Configure

Set environment variables:

```bash
export BOT_TOKEN="your-telegram-bot-token"
export UNSPLASH_ACCESS_KEY="your-unsplash-api-key"  # Optional
```

Or edit `config.py`.

> **Note:** Unsplash API key is optional. The bot works perfectly with cached images or gradient fallback.

> **Railway runtime note:** Python is pinned to `3.12` via `nixpacks.toml` to avoid Pillow build issues on `3.13`. If you configure runtime from Railway UI only, set `NIXPACKS_PYTHON_VERSION=3.12`.

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
+-- main.py                    # Bot entry-point, all command/callback handlers, APScheduler
+-- hadith_card.py             # Renders hadith image cards (PIL); fetches backgrounds via Unsplash or local cache
+-- islamic_images.py          # Pexels-based Islamic image provider (used by older pipeline)
+-- download_islamic_images.py # One-time script to pre-populate .image_cache/ with curated images
+-- tafsir_loader.py           # Tafsir (Quran commentary) data loader helper
+-- user_data.py               # Read/write helpers for user_data.json
+-- config.py                  # All credentials and constants (BOT_TOKEN, API keys, etc.)
+-- requirements.txt           # Python dependencies
+-- user_data.json             # Persistent per-user state (daily time, index, favorites, language)
+-- .image_cache/              # Auto-created; holds pre-downloaded background JPEGs
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

## ⚠️ Known Issues (Active — Needs Fix)

### 1. Images Are Not Islamic

**Symptom:** Hadith cards are sent with random, non-Islamic background images (landscapes, cityscapes, animals, generic stock photos, etc.) instead of Islamic imagery (mosques, Quran, calligraphy, etc.).

**Root causes:**

- **Primary source — Unsplash API (`hadith_card.py`):**  
  `_get_islamic_image()` calls the Unsplash `/photos/random` endpoint with an Islamic keyword, but Unsplash's "random" endpoint is not guaranteed to return an on-topic photo. The `UNSPLASH_ACCESS_KEY` is empty by default (`config.py`), so in most deployments this path is completely skipped and the bot jumps straight to the cached images.

- **Cached images (`download_islamic_images.py`):**  
  The pre-download script contains **duplicate URLs** — the same Unsplash photo IDs are listed three or more times under different comment labels. When the script runs, multiple files with different names (`islamic_01.jpg`, `islamic_03.jpg`, `islamic_10.jpg`) contain identical content. Because `_get_islamic_image()` picks from `os.listdir()` randomly, these pixel-identical non-Islamic images dominate the pool and are selected frequently.

- **Pexels path (`islamic_images.py`):**  
  The `_looks_islamic()` filter examines only the photo's `alt` text for Islamic keywords. Many genuinely Islamic images on Pexels have generic or English alt text (e.g. "brown building") and are rejected. The fallback `_FALLBACK_IMAGES` list contains only **4 hardcoded Pexels URLs** — and those URLs point to generic architecture photos, not verified Islamic content.

---

### 2. The Same Images Keep Repeating

**Symptom:** Users receive the same 1–4 background images repeatedly across multiple hadith requests, even over multiple days.

**Root causes:**

- **`@lru_cache` on `_render_cached()` (`hadith_card.py`):**  
  The cache key is a SHA-256 hash of `lang + text + reference`. `_get_islamic_image()` is called *inside* the cached function, so it is only ever called **once per unique hadith text**. After the first render, every subsequent request for the same hadith returns the exact same JPEG bytes (same background, same layout). The image selection is never revisited.

- **Tiny, duplicate cache pool (`download_islamic_images.py`):**  
  The script lists 12 entries but many are duplicates of the same URL, resulting in only ~5–6 unique files on disk. `random.choice(cache_files)` across this tiny pool causes rapid visible repetition.

- **Small Pexels fallback (`islamic_images.py`):**  
  `_FALLBACK_IMAGES` has only 4 entries. Even with the `_RECENT_URLS` deque (maxlen=40), when the total pool is 4 items, `fresh` becomes empty almost immediately and the same 4 images cycle endlessly.

---

### Summary for the Fixing Agent

| Problem | File(s) to fix | What needs to change |
|---|---|---|
| Non-Islamic images served | `download_islamic_images.py`, `islamic_images.py`, `hadith_card.py` | Replace/verify all curated URLs; strengthen content filtering; validate images at download time |
| Duplicate URLs in cache script | `download_islamic_images.py` | Deduplicate the `CURATED_ISLAMIC_IMAGES` list; add more verified Islamic image URLs |
| `lru_cache` locks in the same background | `hadith_card.py` | Move `_get_islamic_image()` call **outside** `_render_cached()` so each render picks a fresh background; or remove the LRU cache entirely |
| Tiny Pexels fallback pool | `islamic_images.py` | Expand `_FALLBACK_IMAGES` with verified Islamic image URLs (mosque interiors, Quran, calligraphy); or integrate a dedicated Islamic image API |

---

## License

Personal project for Hadith study and reflection.
