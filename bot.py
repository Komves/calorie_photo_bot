from __future__ import annotations

import logging
import os
import socket
import ssl
from io import BytesIO

import certifi
from aiohttp import web
from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ChatAction
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardRemove, Update

from config import Settings
from services.calorie_analyzer import CalorieAnalyzer


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.answer(
        "Привет. Пришли фото, и я постараюсь его разобрать.\n\n"
        "Если это еда — оценю калорийность. Если не еда — просто скажу, что на фото.",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(F.photo)
async def photo_handler(
    message: Message,
    bot: Bot,
    analyzer: CalorieAnalyzer,
    settings: Settings,
) -> None:
    photo = message.photo[-1]

    if photo.file_size and photo.file_size > settings.max_photo_size_mb * 1024 * 1024:
        await message.answer(
            f"Фото слишком большое. Лимит: {settings.max_photo_size_mb} МБ."
        )
        return

    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

    telegram_file = await bot.get_file(photo.file_id)
    if not telegram_file.file_path:
        await message.answer("Не удалось получить файл от Telegram.")
        return

    buffer = BytesIO()
    await bot.download_file(telegram_file.file_path, destination=buffer)
    image_bytes = buffer.getvalue()

    try:
        result = await analyzer.analyze_photo(image_bytes)
    except Exception as exc:
        logging.exception("Photo analysis failed: %s", exc)
        await message.answer("Не получилось обработать фото. Попробуй ещё раз.")
        return

    await message.answer(result)


@router.message()
async def fallback_handler(message: Message) -> None:
    await message.answer("Пришли фото.")


async def health_handler(_: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


async def webhook_handler(request: web.Request) -> web.Response:
    bot: Bot = request.app["bot"]
    dp: Dispatcher = request.app["dp"]

    data = await request.json()
    update = Update.model_validate(data, context={"bot": bot})

    await dp.feed_update(bot, update)
    return web.Response(text="ok")


async def on_startup(app: web.Application) -> None:
    settings = Settings.from_env()
    analyzer = CalorieAnalyzer(api_key=settings.openai_api_key)

    ssl_context = ssl.create_default_context(cafile=certifi.where())

    session = AiohttpSession()
    session._connector_init["ssl"] = ssl_context
    session._connector_init["family"] = socket.AF_INET

    bot = Bot(token=settings.bot_token, session=session)
    dp = Dispatcher()

    dp["analyzer"] = analyzer
    dp["settings"] = settings
    dp.include_router(router)

    base_url = os.getenv("WEBHOOK_BASE_URL", "").strip().rstrip("/")
    if not base_url:
        raise ValueError("WEBHOOK_BASE_URL is not set")

    webhook_url = f"{base_url}/webhook"

    app["bot"] = bot
    app["dp"] = dp
    app["settings"] = settings

    await bot.set_webhook(webhook_url, drop_pending_updates=True)

    logging.info("Webhook set to %s", webhook_url)
    logging.info("Healthcheck server started on 0.0.0.0:%s", os.getenv("PORT", "10000"))


async def on_cleanup(app: web.Application) -> None:
    bot: Bot = app["bot"]
    await bot.session.close()


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/", health_handler)
    app.router.add_get("/healthz", health_handler)
    app.router.add_post("/webhook", webhook_handler)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    return app


def main() -> None:
    port = int(os.getenv("PORT", "10000"))
    web.run_app(create_app(), host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()