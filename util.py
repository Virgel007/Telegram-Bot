import logging
from telegram import (
    InlineKeyboardButton, InlineKeyboardMarkup, Message,
    BotCommandScopeChat, MenuButtonDefault, Update
)
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


def dialog_user_info_to_str(user_data) -> str:
    """Преобразует объект данных пользователя в строковое представление."""
    mapper = {
        'language_from': 'Исходный язык',
        'language_to': 'Язык перевода',
        'text_to_translate': 'Текст для перевода'
    }
    return '\n'.join(f"{mapper[k]}: {v}" for k, v in user_data.items())


async def send_text_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE,
                            text: str, buttons: dict) -> Message:
    """Отправляет текстовое сообщение с встроенными кнопками."""
    text = text.encode('utf16', errors='surrogatepass').decode('utf16')
    keyboard = [
        [InlineKeyboardButton(str(value), callback_data=str(key))]
        for key, value in buttons.items()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return await context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text=text,
        reply_markup=reply_markup
    )


async def send_image(update: Update, context: ContextTypes.DEFAULT_TYPE,
                     name: str) -> Message:
    """Отправляет изображение в чат."""
    with open(f'resources/images/{name}.jpg', 'rb') as image:
        return await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=image
        )


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE,
                         commands: dict):
    """Отображает главное меню с кнопками команд."""
    keyboard = [
        [InlineKeyboardButton(text=value, callback_data=key)]
        for key, value in commands.items()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "Выберите действие:"
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        reply_markup=reply_markup
    )


async def hide_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удаляет команды для конкретного чата."""
    await context.bot.delete_my_commands(
        scope=BotCommandScopeChat(chat_id=update.effective_chat.id)
    )
    await context.bot.set_chat_menu_button(
        menu_button=MenuButtonDefault(),
        chat_id=update.effective_chat.id
    )


def load_message(name) -> str:
    """Загружает сообщение из папки /resources/messages/."""
    try:
        with open(f"resources/messages/{name}.txt", "r", encoding="utf8") as file:
            return file.read()
    except FileNotFoundError:
        logger.error(f"Файл resources/messages/{name}.txt не найден.")
        return "Ошибка: Файл не найден."


def load_prompt(name) -> str:
    """Загружает подсказку из папки /resources/prompts/."""
    try:
        with open(f"resources/prompts/{name}.txt", "r", encoding="utf8") as file:
            return file.read()
    except FileNotFoundError:
        logger.error(f"Файл resources/prompts/{name}.txt не найден.")
        return "Ошибка: Файл не найден."
