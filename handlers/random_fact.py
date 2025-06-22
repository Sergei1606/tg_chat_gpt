from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CallbackContext
from services.openai_service import OpenAIService
from services.image_service import get_image
import logging

logger = logging.getLogger(__name__)

RANDOM_FACT_PROMPT = "Расскажи интересный научный факт на русском языке длиной 2-3 предложения."


async def random_fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /random"""
    try:
        # Отправляем изображение
        image_path = get_image("random_fact")
        with open(image_path, 'rb') as photo:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=photo
            )

        # Получаем факт от ChatGPT
        fact = await OpenAIService.get_chatgpt_response(RANDOM_FACT_PROMPT)

        # Создаем клавиатуру
        keyboard = [
            [InlineKeyboardButton("Хочу ещё факт", callback_data="random_again")],
            [InlineKeyboardButton("Закончить", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=fact,
            reply_markup=reply_markup
        )
        logger.info(f"Sent random fact to user {update.effective_user.id}")

    except Exception as e:
        logger.error(f"Error in random_fact: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Произошла ошибка при получении факта. Попробуйте позже."
        )


async def random_fact_callback(update: Update, context: CallbackContext):
    """Обработчик callback для кнопок в /random"""
    query = update.callback_query
    await query.answer()

    if query.data == "random_again":
        await random_fact(update, context)