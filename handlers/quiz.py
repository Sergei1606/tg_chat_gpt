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
import re

logger = logging.getLogger(__name__)

# Состояния ConversationHandler
SELECTING_TOPIC = 1
ANSWERING_QUESTION = 2

# Темы для квиза
QUIZ_TOPICS = {
    "geography": {
        "name": "🌍 География",
        "emoji": "🌍",
        "prompt": """Ты создаешь вопросы для квиза по географии.
Создай один интересный географический вопрос средней сложности с 4 вариантами ответа (A, B, C, D).
Укажи правильный ответ в конце.
Формат:
Вопрос: [твой вопрос]
A) [вариант 1]
B) [вариант 2]
C) [вариант 3]
D) [вариант 4]
Правильный ответ: [буква]"""
    },
    "history": {
        "name": "🏛 История",
        "emoji": "🏛",
        "prompt": """Создай исторический вопрос с 4 вариантами ответа.
Укажи правильный ответ в конце.
Формат:
Вопрос: [твой вопрос]
A) [вариант 1]
B) [вариант 2]
C) [вариант 3]
D) [вариант 4]
Правильный ответ: [буква]"""
    }
}


async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /quiz с отправкой изображения"""
    try:
        # Отправляем изображение
        image_path = get_image("quiz")
        with open(image_path, 'rb') as photo:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=photo
            )
    except Exception as e:
        logger.error(f"Error sending image in quiz_command: {e}")

    # Инициализация счета
    context.user_data["quiz_score"] = 0

    # Создаем клавиатуру с темами
    keyboard = [
        [InlineKeyboardButton(
            f"{topic['name']} {topic['emoji']}",
            callback_data=f"quiz_topic_{key}"
        )]
        for key, topic in QUIZ_TOPICS.items()
    ]
    keyboard.append([InlineKeyboardButton("Отмена", callback_data="main_menu")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Выберите тему викторины:",
        reply_markup=reply_markup
    )
    return SELECTING_TOPIC


async def topic_selected(update: Update, context: CallbackContext):
    """Обработка выбора темы"""
    query = update.callback_query
    await query.answer()

    topic_key = query.data.split("_")[2]
    topic = QUIZ_TOPICS.get(topic_key)

    if not topic:
        await query.edit_message_text("Ошибка: тема не найдена")
        return ConversationHandler.END

    context.user_data["current_topic"] = topic
    context.user_data["current_topic_key"] = topic_key

    # Запрашиваем вопрос у ChatGPT
    await ask_new_question(update, context)
    return ANSWERING_QUESTION


async def ask_new_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Получаем сообщение или callback query
        if update.message:
            chat_id = update.message.chat.id
            reply_method = update.message.reply_text
        else:
            query = update.callback_query
            await query.answer()
            chat_id = query.message.chat.id
            reply_method = context.bot.send_message

        # Остальная логика...

    except Exception as e:
        logger.error(f"Error in ask_new_question: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text="Произошла ошибка при получении вопроса."
        )
        return ConversationHandler.END


async def handle_quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка ответа пользователя"""
    user_answer = update.message.text.upper()
    correct_answer = context.user_data.get("correct_answer", "")

    # Проверяем ответ
    if user_answer == correct_answer:
        context.user_data["quiz_score"] += 1
        result_text = "✅ Правильно! 🎉"
    else:
        result_text = f"❌ Неправильно. Правильный ответ: {correct_answer}"

    # Добавляем текущий счет
    score = context.user_data["quiz_score"]
    result_text += f"\n\nВаш счет: {score}"

    # Кнопки для продолжения
    keyboard = [
        [
            InlineKeyboardButton("Следующий вопрос",
                                 callback_data=f"quiz_next_{context.user_data['current_topic_key']}"),
            InlineKeyboardButton("Сменить тему", callback_data="quiz_change_topic")
        ],
        [InlineKeyboardButton("Закончить", callback_data="quiz_finish")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=result_text,
        reply_markup=reply_markup
    )
    return ANSWERING_QUESTION


async def handle_quiz_callback(update: Update, context: CallbackContext):
    """Обработка callback-кнопок викторины"""
    query = update.callback_query
    await query.answer()

    if query.data == "quiz_finish":
        score = context.user_data.get("quiz_score", 0)
        await query.edit_message_text(
            f"Викторина завершена! Ваш итоговый счет: {score}\n"
            "Используйте /start для возврата в меню."
        )
        return ConversationHandler.END

    elif query.data.startswith("quiz_next_"):
        # Запрашиваем новый вопрос по текущей теме
        return await ask_new_question(update, context)

    elif query.data == "quiz_change_topic":
        # Возвращаемся к выбору темы
        return await quiz_command(update, context)

    return ANSWERING_QUESTION