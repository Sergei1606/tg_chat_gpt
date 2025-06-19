from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes,
    CallbackContext,
    ConversationHandler,
    MessageHandler,
    filters
)
from services.openai_service import OpenAIService
import logging

logger = logging.getLogger(__name__)

# Состояния ConversationHandler
WAITING_FOR_MESSAGE = 1


async def gpt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /gpt"""
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Отправьте мне сообщение, и я передам его ChatGPT:"
    )
    return WAITING_FOR_MESSAGE


async def gpt_start(update: Update, context: CallbackContext):
    """Начало диалога через callback"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        text="Отправьте мне сообщение, и я передам его ChatGPT:"
    )
    return WAITING_FOR_MESSAGE


async def handle_gpt_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка сообщения для ChatGPT"""
    user_message = update.message.text

    keyboard = [
        [InlineKeyboardButton("Закончить", callback_data="gpt_finish")],
        [InlineKeyboardButton("Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        response = await OpenAIService.get_chatgpt_response(user_message)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=response,
            reply_markup=reply_markup
        )
        logger.info(f"Processed GPT request for user {update.effective_user.id}")
    except Exception as e:
        logger.error(f"Error in handle_gpt_message: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Произошла ошибка при обработке запроса."
        )

    return WAITING_FOR_MESSAGE