# Calorie Photo Bot

Минимальный Telegram-бот на aiogram 3, который принимает фото еды и просит OpenAI оценить калорийность.

## Локальный запуск

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python bot.py
```

Заполни `.env`:

```env
BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
MAX_PHOTO_SIZE_MB=10
```

## Deploy на Render

1. Загрузи проект в GitHub.
2. В Render выбери **New Blueprint**.
3. Подключи репозиторий.
4. Render прочитает `render.yaml`.
5. В Environment Variables задай:
   - `BOT_TOKEN`
   - `OPENAI_API_KEY`

## Структура

```text
calorie_photo_bot/
├─ bot.py
├─ config.py
├─ requirements.txt
├─ render.yaml
├─ .env.example
├─ .gitignore
├─ README.md
└─ services/
   ├─ __init__.py
   └─ calorie_analyzer.py
```
