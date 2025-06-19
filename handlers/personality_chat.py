from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes,
    CallbackContext,
    ConversationHandler,
    MessageHandler,
    filters
)
from services.openai_service import OpenAIService
from services.image_service import get_image
import logging

logger = logging.getLogger(__name__)

# Состояния ConversationHandler
SELECTING_PERSONALITY = 1
CHATTING_WITH_PERSONALITY = 2

# Промпты для личностей (можно вынести в отдельный файл)
PERSONALITIES = {
    "einstein": {
        "name": "Альберт Эйнштейн",
        "emoji": "🧬",
        "prompt": (
            "Ты - Альберт Эйнштейн, великий физик и мыслитель. "
            "Отвечай как он: мудро, с юмором, философски. "
            "Используй метафоры и аналогии для объяснения сложных концепций. "
            "Говори на русском языке, но иногда вставляй немецкие фразы. "
            "Проявляй любопытство к миру и поощряй творческое мышление."
        )
    },
    "pushkin": {
        "name": "Александр Пушкин",
        "emoji": "📝",
        "prompt": (
            "Ты - Александр Сергеевич Пушкин, великий русский поэт. "
            "Отвечай в стиле XIX века, используй красивый литературный русский язык. "
            "Говори о поэзии, любви, природе, России. "
            "Будь остроумным, галантным и слегка ироничным. "
            "Иногда цитируй свои произведения или говори в стихотворной форме."
        )
    }
}


async def talk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /talk с отправкой изображения"""
    try:
        # Отправляем изображение
        image_path = get_image("talk")
        with open(image_path, 'rb') as photo:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=photo
            )
    except Exception as e:
        logger.error(f"Error sending image in talk_command: {e}")

    # Создаем клавиатуру с личностями
    keyboard = [
        [InlineKeyboardButton(
            f"{personality['name']} {personality['emoji']}",
            callback_data=f"personality_{key}"
        )]
        for key, personality in PERSONALITIES.items()
    ]
    keyboard.append([InlineKeyboardButton("Отмена", callback_data="main_menu")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Выберите личность для диалога:",
        reply_markup=reply_markup
    )
    return SELECTING_PERSONALITY


async def personality_selected(update: Update, context: CallbackContext):
    """Обработка выбора личности"""
    query = update.callback_query
    await query.answer()

    personality_key = query.data.split("_")[1]
    personality = PERSONALITIES.get(personality_key)

    if not personality:
        await query.edit_message_text("Ошибка: личность не найдена")
        return ConversationHandler.END

    context.user_data["current_personality"] = personality

    # Кнопки для управления диалогом
    keyboard = [
        [InlineKeyboardButton("Закончить диалог", callback_data="finish_talk")],
        [InlineKeyboardButton("Сменить личность", callback_data="change_personality")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text=f"Вы выбрали: {personality['name']}\n\n"
             "Теперь отправляйте сообщения, и я буду отвечать как эта личность.\n"
             "Можете закончить диалог или сменить личность кнопками ниже:",
        reply_markup=reply_markup
    )
    return CHATTING_WITH_PERSONALITY


async def handle_personality_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка сообщений в режиме диалога с личностью"""
    user_message = update.message.text
    personality = context.user_data.get("current_personality")

    if not personality:
        await update.message.reply_text("Пожалуйста, сначала выберите личность с помощью /talk")
        return ConversationHandler.END

    try:
        # Получаем ответ от ChatGPT в стиле выбранной личности
        response = await OpenAIService.get_chatgpt_response(
            prompt=user_message,
            context=personality["prompt"]
        )

        # Кнопки для управления диалогом
        keyboard = [
            [InlineKeyboardButton("Закончить диалог", callback_data="finish_talk")],
            [InlineKeyboardButton("Сменить личность", callback_data="change_personality")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=response,
            reply_markup=reply_markup
        )
        logger.info(f"User {update.effective_user.id} chatted with {personality['name']}")

    except Exception as e:
        logger.error(f"Error in handle_personality_message: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Произошла ошибка при обработке сообщения."
        )

    return CHATTING_WITH_PERSONALITY


async def handle_personality_callback(update: Update, context: CallbackContext):
    """Обработка callback-кнопок во время диалога"""
    query = update.callback_query
    await query.answer()

    if query.data == "finish_talk":
        await query.edit_message_text("Диалог завершен. Используйте /start для возврата в меню.")
        return ConversationHandler.END

    elif query.data == "change_personality":
        # Возвращаемся к выбору личности
        return await talk_command(update, context)

    return CHATTING_WITH_PERSONALITY