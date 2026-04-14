from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    bot_token: str
    openai_api_key: str
    max_photo_size_mb: int

    @classmethod
    def from_env(cls) -> "Settings":
        bot_token = os.getenv("BOT_TOKEN", "").strip()
        openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
        max_photo_size_mb_raw = os.getenv("MAX_PHOTO_SIZE_MB", "10").strip()

        if not bot_token:
            raise ValueError("BOT_TOKEN is not set")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY is not set")

        try:
            max_photo_size_mb = int(max_photo_size_mb_raw)
        except ValueError as exc:
            raise ValueError("MAX_PHOTO_SIZE_MB must be an integer") from exc

        if max_photo_size_mb <= 0:
            raise ValueError("MAX_PHOTO_SIZE_MB must be greater than 0")

        return cls(
            bot_token=bot_token,
            openai_api_key=openai_api_key,
            max_photo_size_mb=max_photo_size_mb,
        )
