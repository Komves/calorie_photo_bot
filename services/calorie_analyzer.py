from __future__ import annotations

import base64

from openai import AsyncOpenAI


MODEL_NAME = "gpt-5.4"

SYSTEM_PROMPT = (
    "Ты помощник по оценке калорийности еды по фото. "
    "Отвечай по-русски. "
    "Это должна быть примерная оценка, а не точный медицинский расчёт. "
    "Если на фото не еда или еды не видно достаточно ясно, честно скажи об этом. "
    "Не придумывай лишние детали. "
    "Ответ должен быть коротким и полезным.\n\n"
    "Формат ответа:\n"
    "1. Что изображено\n"
    "2. Примерная калорийность всей порции\n"
    "3. Очень кратко: белки / жиры / углеводы\n"
    "4. Короткая оговорка о погрешности"
)


class CalorieAnalyzer:
    def __init__(self, api_key: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key)

    async def analyze_photo(self, image_bytes: bytes) -> str:
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        image_data_url = f"data:image/jpeg;base64,{base64_image}"

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
                                "Оцени калорийность еды на фото. "
                                "Если блюд несколько, оцени суммарно и по возможности кратко по частям."
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
