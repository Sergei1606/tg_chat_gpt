from telegram import Update, ReplyKeyboardMarkup
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
GETTING_NAME = 1
GETTING_EDUCATION = 2
GETTING_EXPERIENCE = 3
GETTING_SKILLS = 4


async def resume_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /resume"""
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Помогу составить резюме. Введите ваше ФИО:"
    )
    return GETTING_NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение имени"""
    context.user_data["name"] = update.message.text

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Введите ваше образование (учебные заведения, годы обучения):"
    )
    return GETTING_EDUCATION


async def get_education(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение образования"""
    context.user_data["education"] = update.message.text

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Опишите ваш опыт работы (места работы, должности, периоды):"
    )
    return GETTING_EXPERIENCE


async def get_experience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение опыта работы"""
    context.user_data["experience"] = update.message.text

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Перечислите ваши ключевые навыки (через запятую):"
    )
    return GETTING_SKILLS


async def get_skills(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение навыков и генерация резюме"""
    context.user_data["skills"] = update.message.text

    try:
        prompt = (
            "Составь профессиональное резюме на основе следующих данных:\n"
            f"ФИО: {context.user_data['name']}\n"
            f"Образование: {context.user_data['education']}\n"
            f"Опыт работы: {context.user_data['experience']}\n"
            f"Навыки: {context.user_data['skills']}\n\n"
            "Резюме должно быть структурированным, профессиональным "
            "и подходящим для размещения на hh.ru. Используй markdown для форматирования."
        )

        resume = await OpenAIService.get_chatgpt_response(prompt)

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=resume,
            parse_mode="Markdown"
        )
        logger.info(f"Generated resume for user {update.effective_user.id}")
    except Exception as e:
        logger.error(f"Error in get_skills: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Произошла ошибка при генерации резюме."
        )

    return ConversationHandler.END