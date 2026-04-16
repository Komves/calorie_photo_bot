from __future__ import annotations

import base64

from openai import AsyncOpenAI


MODEL_NAME = "gpt-5.4"

SYSTEM_PROMPT = (
    "Ты помощник по анализу изображений. "
    "Отвечай по-русски, кратко и по делу.\n\n"
    "Если на фото ЕДА:\n"
    "1. Что изображено\n"
    "2. Примерная калорийность всей порции\n"
    "3. Кратко: белки / жиры / углеводы\n"
    "4. Полезный совет\n"
    "5. Оценка блюда по шкале 1–10\n\n"
    "Если на фото НЕ еда:\n"
    "1. Что изображено\n"
    "2. Краткое описание\n"
    "3. Важные детали\n"
    "4. Полезная информация или советы\n\n"
    "Если не уверен — честно скажи и предложи варианты."
)


class CalorieAnalyzer:
    def __init__(self, api_key: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key)

    @staticmethod
    def _detect_mime(image_bytes: bytes) -> str:
        return "image/jpeg"

    async def analyze_photo(self, image_bytes: bytes) -> str:
        mime_type = self._detect_mime(image_bytes)
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        image_data_url = f"data:{mime_type};base64,{base64_image}"

        response = await self._client.responses.create(
            model=MODEL_NAME,
            instructions=SYSTEM_PROMPT,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "Проанализируй изображение и определи, что на нём. "
                                "Если это еда — оцени калорийность. "
                                "Если нет — просто объясни, что изображено."
                            ),
                        },
                        {
                            "type": "input_image",
                            "image_url": image_data_url,
                        },
                    ],
                }
            ],
        )

        result = (response.output_text or "").strip()
        if not result:
            return "Не удалось получить ответ от модели."
        return result