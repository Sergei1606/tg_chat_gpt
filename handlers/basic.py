from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup
)
from telegram.ext import (
    ContextTypes,
    CallbackContext,
    CommandHandler,
    CallbackQueryHandler
)
import logging

logger = logging.getLogger(__name__)


# Клавиатура для главного меню
def create_main_menu_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎲 Случайный факт", callback_data="random_fact"),
            InlineKeyboardButton("💬 Чат с GPT", callback_data="gpt_interface")
        ],
        [
            InlineKeyboardButton("🧑‍🎨 Диалог с личностью", callback_data="talk_interface"),
            InlineKeyboardButton("🧩 Викторина", callback_data="quiz_interface")
        ],
        [
            InlineKeyboardButton("🌍 Переводчик", callback_data="translate_interface"),
            InlineKeyboardButton("📄 Помощь с резюме", callback_data="resume_interface")
        ]
    ])


# Клавиатура для быстрого доступа (ReplyKeyboard)
def create_reply_keyboard():
    return ReplyKeyboardMarkup([
        ["/random", "/gpt"],
        ["/talk", "/quiz"],
        ["/translate", "/resume"]
    ], resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start - главное меню"""
    try:
        welcome_text = (
            "👋 Привет! Я умный бот с интеграцией ChatGPT.\n\n"
            "Выбери действие из меню ниже или используй команды:\n"
            "• /random - Интересный факт\n"
            "• /gpt - Чат с ИИ\n"
            "• /talk - Диалог с известной личностью\n"
            "• /quiz - Викторина\n"
            "• /translate - Переводчик\n"
            "• /resume - Помощь с резюме\n\n"
            "Или просто нажми на кнопки внизу экрана!"
        )

        # Отправляем сообщение с инлайн-клавиатурой
        if update.message:
            await update.message.reply_text(
                text=welcome_text,
                reply_markup=create_main_menu_keyboard()
            )
            # Добавляем reply-клавиатуру для быстрого доступа
            await update.message.reply_text(
                "Используйте кнопки ниже:",
                reply_markup=create_reply_keyboard()
            )
        elif update.callback_query:
            await update.callback_query.message.reply_text(
                text=welcome_text,
                reply_markup=create_main_menu_keyboard()
            )

        logger.info(f"User {update.effective_user.id} started the bot")

    except Exception as e:
        logger.error(f"Error in start handler: {e}")
        if update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Произошла ошибка при загрузке меню. Попробуйте позже."
            )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help - справка"""
    help_text = (
        "ℹ️ <b>Доступные команды:</b>\n\n"
        "<b>Основные команды:</b>\n"
        "/start - Главное меню\n"
        "/help - Эта справка\n\n"
        "<b>Функции бота:</b>\n"
        "/random - Интересный факт с картинкой\n"
        "/gpt - Чат с искусственным интеллектом\n"
        "/talk - Диалог с известной личностью\n"
        "/quiz - Викторина на разные темы\n"
        "/translate - Переводчик текста\n"
        "/resume - Помощь с составлением резюме\n\n"
        "Также вы можете использовать кнопки меню!"
    )

    try:
        await update.message.reply_text(
            text=help_text,
            parse_mode="HTML",
            reply_markup=create_reply_keyboard()
        )
    except Exception as e:
        logger.error(f"Error in help handler: {e}")


async def menu_callback(update: Update, context: CallbackContext):
    """Обработчик callback-запросов главного меню"""
    try:
        query = update.callback_query
        await query.answer()

        # Проверяем, не пытаемся ли изменить на такое же сообщение
        current_text = query.message.text
        if "Выберите действие:" in current_text:
            return

        await query.edit_message_text(
            text="Выберите действие:",
            reply_markup=create_main_menu_keyboard()
        )

    except Exception as e:
        logger.error(f"Error in menu callback: {e}")
        try:
            await query.answer("Произошла ошибка")
        except:
            pass


def setup_handlers(application):
    """Регистрация обработчиков для основного меню"""
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(menu_callback, pattern="^main_menu$"))