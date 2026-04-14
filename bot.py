from __future__ import annotations

import asyncio
import logging
import socket
import sys
from io import BytesIO

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ChatAction
from aiogram.filters import CommandStart
from aiogram.types import Message

from config import Settings
from services.calorie_analyzer import CalorieAnalyzer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

router = Router()


from aiogram.types import ReplyKeyboardRemove

@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.answer(
        "Привет. Пришли фото еды, и я оценю калорийность.\n\n"
        "Важно: это примерная оценка, а не точный диетологический расчёт.",
        reply_markup=ReplyKeyboardRemove()
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
    await message.answer("Пришли именно фото еды.")


async def main() -> None:
    settings = Settings.from_env()
    analyzer = CalorieAnalyzer(api_key=settings.openai_api_key)

    session = AiohttpSession()
    session._connector_init["family"] = socket.AF_INET

    bot = Bot(token=settings.bot_token, session=session)
    dp = Dispatcher()

    dp["analyzer"] = analyzer
    dp["settings"] = settings
    dp.include_router(router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
