import openai
from config import CHATGPT_TOKEN
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Инициализация клиента OpenAI
client = openai.AsyncOpenAI(api_key=CHATGPT_TOKEN)


class OpenAIService:
    @staticmethod
    async def get_chatgpt_response(
            prompt: str,
            context: Optional[str] = None,
            model: str = "gpt-3.5-turbo",
            temperature: float = 0.7
    ) -> str:
        """
        Получает ответ от ChatGPT через новое API (асинхронная версия).

        Args:
            prompt: Текст запроса пользователя
            context: Контекст для системы (опционально)
            model: Модель ChatGPT
            temperature: Креативность ответов

        Returns:
            Ответ от ChatGPT
        """
        try:
            messages = []

            if context:
                messages.append({"role": "system", "content": context})

            messages.append({"role": "user", "content": prompt})

            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise Exception(f"Не удалось получить ответ от ChatGPT. Ошибка: {str(e)}")