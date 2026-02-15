# 🕌 Коран и Тафсир — Telegram Bot

Минималистичный Telegram-бот с ежедневными аятами, полным тафсиром и хадисами.

## Возможности

- 📖 **Telegram Mini App** — Полный тафсир аль-Куртуби и аль-Кушайри
- 📅 **Автоматические сообщения** — 10 аятов в день по расписанию
- 🇷🇺 **Русский язык** — Все переводы через Google Translate
- 🔖 **Закладки** — Сохраняйте любимые аяты
- ⬅️➡️ **Навигация** — Листайте аяты кнопками

## Команды

| Команда | Описание |
|---------|----------|
| `/random` | Случайный аят с тафсиром |
| `/hadith` | Случайный хадис из Сахих аль-Бухари |
| `/bookmarks` | Просмотр сохранённых аятов |

## Быстрый старт

```bash
pip install -r requirements.txt
python main.py
```

Запускает одновременно:
- ✅ Telegram бот (polling)
- ✅ Flask сервер (порт 5000, Mini App)
- ✅ Планировщик (автоматические аяты)

## Переменные окружения

```bash
export BOT_TOKEN="your-telegram-bot-token"
export CHAT_ID="your-telegram-chat-id"
export WEBAPP_URL="https://your-domain.com"
```

## Структура

```
├── main.py              # Бот + Flask + планировщик
├── config.py            # Настройки
├── tafsir_loader.py     # Загрузка тафсира из JSON
├── user_data.py         # Закладки и данные пользователей
├── webapp/
│   └── index.html       # Mini App (тафсир)
├── ar-tafseer-al-qurtubi/  # Тафсир аль-Куртуби (114 сур)
└── en-al-qushairi-tafsir/  # Тафсир аль-Кушайри (114 сур)
```

## API

- `GET /api/tafsir?surah=1&ayah=1` — Полный тафсир (JSON)
- `GET /api/surah-list` — Список всех 114 сур
- `GET /api/health` — Статус сервера

## Технологии

- **python-telegram-bot** — Telegram Bot API
- **Flask** — Веб-сервер для Mini App
- **APScheduler** — Планировщик сообщений
- **deep-translator** — Google Translate (бесплатно)
