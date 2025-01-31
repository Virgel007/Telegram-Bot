from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import logging

logger = logging.getLogger(__name__)


async def send_text(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> Message:
    """
    Send a text message to the user.

    Args:
    - update: The update object from the telegram bot.
    - context: The context of the telegram bot.
    - text: The text to send.

    Returns:
    - Message: The message object.
    """
    if isinstance(text, str) and text.count('_') % 2 != 0:
        message = f"Строка '{text}' недействительна для markdown. Используйте send_html() вместо этого."
        logger.warning(message)
        return await update.message.reply_text(message)
    text = text.encode('utf16', errors='surrogatepass').decode('utf16') if isinstance(text, str) else text
    return await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        parse_mode=ParseMode.MARKDOWN if isinstance(text, str) else None
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    The start function is the entry point of the telegram bot.

    Args:
    - update: The update object from the telegram bot.
    - context: The context of the telegram bot.
    """
    from task.credentials import BOT_TOKEN, ChatGPT_TOKEN
    from gpt import ChatGptService
    from util import load_message, send_image, show_main_menu

    chat_gpt = ChatGptService(ChatGPT_TOKEN)

    text = load_message('main')
    await send_image(update, context, 'main')
    await send_text(update, context, text)
    await show_main_menu(update, context, {
        'start': 'Главное меню',
        'random': 'Узнать рандомный факт',
        'gpt': 'Задать вопрос ChatGPT',
        'talk': 'Поговорить с известной личностью',
        'quiz': 'Пройти викторину',
        'translate': 'Переводчик'
    })


async def send_text_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, buttons: dict) -> Message:
    """
    Send a text message with buttons to the user.

    Args:
    - update: The update object from the telegram bot.
    - context: The context of the telegram bot.
    - text: The text to send.
    - buttons: The buttons to send.

    Returns:
    - Message: The message object.
    """
    text = text.encode('utf16', errors='surrogatepass').decode('utf16')
    keyboard = []
    for key, value in buttons.items():
        button = InlineKeyboardButton(str(value), callback_data=str(key))
        keyboard.append([button])
    reply_markup = InlineKeyboardMarkup(keyboard)
    return await context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text=text,
        reply_markup=reply_markup
    )


async def send_image(update: Update, context: ContextTypes.DEFAULT_TYPE, name: str) -> Message:
    """
    Send an image to the user.

    Args:
    - update: The update object from the telegram bot.
    - context: The context of the telegram bot.
    - name: The name of the image.

    Returns:
    - Message: The message object.
    """
    with open(f'resources/images/{name}.jpg', 'rb') as image:
        return await context.bot.send_photo(chat_id=update.effective_chat.id,
                                            photo=image)


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, commands: dict):
    """
    Show the main menu of the telegram bot.

    Args:
    - update: The update object from the telegram bot.
    - context: The context of the telegram bot.
    - commands: The commands to show in the main menu.
    """
    buttons = {key: value for key, value in commands.items()}
    keyboard = [[InlineKeyboardButton(text=value, callback_data=key)] for key, value in buttons.items()]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = "Выберите действие:"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=reply_markup)