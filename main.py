import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from telegram.warnings import PTBUserWarning
from warnings import filterwarnings

# Импорт обработчиков
from handlers.basic import start, help_command, menu_callback
from handlers.random_fact import random_fact, random_fact_callback
from handlers.chatgpt_interface import (
    gpt_command,
    gpt_start,
    handle_gpt_message,
    WAITING_FOR_MESSAGE as GPT_WAITING
)
from handlers.personality_chat import (
    talk_command,
    personality_selected,
    handle_personality_message,
    handle_personality_callback,
    SELECTING_PERSONALITY,
    CHATTING_WITH_PERSONALITY
)
from handlers.quiz import (
    quiz_command,
    topic_selected,
    ask_new_question,
    handle_quiz_answer,
    handle_quiz_callback,
    SELECTING_TOPIC,
    ANSWERING_QUESTION
)
from handlers.translator import (
    translate_command,
    language_selected,
    handle_translation_text,
    change_language,
    SELECTING_LANGUAGE,
    WAITING_FOR_TEXT as TRANS_WAITING
)
from handlers.resume_helper import (
    resume_command,
    get_name,
    get_education,
    get_experience,
    get_skills,
    GETTING_NAME,
    GETTING_EDUCATION,
    GETTING_EXPERIENCE,
    GETTING_SKILLS
)
from config import TG_BOT_TOKEN

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Игнорирование предупреждений PTB
filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Update {update} caused error {context.error}")
    try:
        if update.callback_query:
            await update.callback_query.answer("Произошла ошибка")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Произошла ошибка. Пожалуйста, попробуйте позже."
        )
    except Exception as e:
        logger.error(f"Error in error handler: {e}")

def create_gpt_conversation():
    """Создает ConversationHandler для GPT интерфейса"""
    return ConversationHandler(
        entry_points=[
            CommandHandler("gpt", gpt_command),
            CallbackQueryHandler(gpt_start, pattern="^gpt_")
        ],
        states={
            GPT_WAITING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_gpt_message)
            ],
        },
        fallbacks=[
            CommandHandler("start", start),
            CallbackQueryHandler(menu_callback, pattern="^(gpt_finish|main_menu)$")
        ],
        per_message=True,
    )

def create_personality_conversation():
    """Создает ConversationHandler для диалога с личностью"""
    return ConversationHandler(
        entry_points=[
            CommandHandler("talk", talk_command),
            CallbackQueryHandler(talk_command, pattern="^talk_")
        ],
        states={
            SELECTING_PERSONALITY: [
                CallbackQueryHandler(personality_selected, pattern="^personality_")
            ],
            CHATTING_WITH_PERSONALITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_personality_message),
                CallbackQueryHandler(handle_personality_callback,
                                   pattern="^(finish_talk|change_personality)$")
            ],
        },
        fallbacks=[
            CommandHandler("start", start),
            CallbackQueryHandler(menu_callback, pattern="^main_menu$")
        ],
    )

def create_quiz_conversation():
    """Создает ConversationHandler для квиза"""
    return ConversationHandler(
        entry_points=[
            CommandHandler("quiz", quiz_command),
            CallbackQueryHandler(quiz_command, pattern="^quiz_")
        ],
        states={
            SELECTING_TOPIC: [
                CallbackQueryHandler(topic_selected, pattern="^quiz_topic_")
            ],
            ANSWERING_QUESTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_quiz_answer),
                CallbackQueryHandler(handle_quiz_callback,
                                   pattern="^(quiz_next_|quiz_change_topic|quiz_finish)$")
            ],
        },
        fallbacks=[
            CommandHandler("start", start),
            CallbackQueryHandler(menu_callback, pattern="^main_menu$")
        ],
    )

def create_translator_conversation():
    """Создает ConversationHandler для переводчика"""
    return ConversationHandler(
        entry_points=[CommandHandler("translate", translate_command)],
        states={
            SELECTING_LANGUAGE: [
                CallbackQueryHandler(language_selected, pattern="^lang_")
            ],
            TRANS_WAITING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_translation_text),
                CallbackQueryHandler(change_language, pattern="^change_lang$")
            ],
        },
        fallbacks=[
            CallbackQueryHandler(menu_callback, pattern="^main_menu$")
        ],
    )

def create_resume_conversation():
    """Создает ConversationHandler для помощника по резюме"""
    return ConversationHandler(
        entry_points=[CommandHandler("resume", resume_command)],
        states={
            GETTING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            GETTING_EDUCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_education)],
            GETTING_EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_experience)],
            GETTING_SKILLS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_skills)],
        },
        fallbacks=[
            CommandHandler("start", start),
            CallbackQueryHandler(menu_callback, pattern="^main_menu$")
        ],
    )

def main():
    """Основная функция запуска бота"""
    try:
        # Создаем приложение
        application = Application.builder().token(TG_BOT_TOKEN).build()

        # Базовые команды
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("random", random_fact))

        # ConversationHandler
        application.add_handler(create_gpt_conversation())
        application.add_handler(create_personality_conversation())
        application.add_handler(create_quiz_conversation())
        application.add_handler(create_translator_conversation())
        application.add_handler(create_resume_conversation())

        # Обработчики callback-запросов
        application.add_handler(CallbackQueryHandler(random_fact_callback, pattern="^random_"))
        application.add_handler(CallbackQueryHandler(menu_callback))

        # Обработчик ошибок
        application.add_error_handler(error_handler)

        # Запуск бота
        logger.info("Бот запущен успешно!")
        application.run_polling()

    except Exception as e:
        logger.error(f'Ошибка при запуске бота: {e}')

if __name__ == "__main__":
    main()