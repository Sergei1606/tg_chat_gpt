from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
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
SELECTING_LANGUAGE = 1
WAITING_FOR_TEXT = 2

# Доступные языки перевода
LANGUAGES = {
    "en": "Английский 🇬🇧",
    "ru": "Русский 🇷🇺",
    "et": "Эстонский 🇪🇪"
}


async def translate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /translate - выбор языка"""
    keyboard = [
        [InlineKeyboardButton(name, callback_data=f"lang_{code}")]
        for code, name in LANGUAGES.items()
    ]
    keyboard.append([InlineKeyboardButton("Отмена", callback_data="main_menu")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Выберите язык для перевода:",
        reply_markup=reply_markup
    )
    return SELECTING_LANGUAGE


async def language_selected(update: Update, context: CallbackContext):
    """Обработка выбора языка"""
    query = update.callback_query
    await query.answer()

    # Извлекаем код языка из callback_data (формат "lang_en")
    lang_code = query.data.split("_")[1]

    if lang_code not in LANGUAGES:
        await query.edit_message_text("Ошибка выбора языка")
        return ConversationHandler.END

    context.user_data["target_language"] = lang_code

    await query.edit_message_text(
        text=f"Выбран язык: {LANGUAGES[lang_code]}\n\nОтправьте текст для перевода:"
    )
    return WAITING_FOR_TEXT


async def handle_translation_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текста для перевода"""
    text_to_translate = update.message.text
    target_lang = context.user_data.get("target_language")

    if not target_lang:
        await update.message.reply_text("Сначала выберите язык через /translate")
        return ConversationHandler.END

    try:
        prompt = f"Переведи текст на {LANGUAGES[target_lang]}: {text_to_translate}"
        translation = await OpenAIService.get_chatgpt_response(prompt)

        keyboard = [
            [InlineKeyboardButton("🔄 Сменить язык", callback_data="change_lang")],
            [InlineKeyboardButton("🏠 В меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            translation,
            reply_markup=reply_markup
        )
        logger.info(f"Translated text for user {update.effective_user.id}")

    except Exception as e:
        logger.error(f"Error in translation: {e}")
        await update.message.reply_text("Произошла ошибка при переводе")

    return WAITING_FOR_TEXT


async def change_language(update: Update, context: CallbackContext):
    """Смена языка перевода"""
    query = update.callback_query
    await query.answer()
    return await translate_command(update, context)