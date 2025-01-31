import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, \
    filters
from credentials import ChatGPT_TOKEN, BOT_TOKEN
from gpt import ChatGptService
from common import send_text, send_image, send_text_buttons, start
from util import load_message, load_prompt

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize bot and GPT service
chat_gpt = ChatGptService(ChatGPT_TOKEN)
app = ApplicationBuilder().token(BOT_TOKEN).build()


# Main menu handler
async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    logger.info("Handling main menu selection")
    query = update.callback_query
    await query.answer()
    command = query.data
    if command == 'start':
        await start(update, context)
    elif command == 'random':
        await random_fact(update, context)
    elif command == 'gpt':
        await question_chat_gpt(update, context)
    elif command == 'talk':
        await personality_menu(update, context)
    elif command == 'quiz':
        await quiz(update, context)
    elif command == 'translate':
        await translate(update, context)
    else:
        await send_text(update, context, "Неизвестная команда")


# Conversation handler
async def handle_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Handling conversation")

    if 'current_topic' in context.user_data:
        await answer_quiz(update, context)
        return

    if 'current_language' in context.user_data:
        await translate_text(update, context)
        return

    if 'current_personality' in context.user_data:
        await personality_talk(update, context)
        return


# Command random fact


async def random_fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Handling /random command")
    text = load_message('random')
    await send_image(update, context, 'random')
    await send_text(update, context, text)
    fact = await chat_gpt.send_question(load_prompt('random'), '')
    await send_text(update, context, fact)
    await send_text_buttons(update, context, "Выберите действие:", {
        'start': 'Главное меню',
        'random': 'Ещё факт'
    })


# Question ChatGPT
async def question_chat_gpt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Handling /gpt command")
    if not context.args:
        await send_text(update, context, "Пожалуйста, укажите ваш вопрос после команды /gpt")
        return
    question = ' '.join(context.args)
    answer = await chat_gpt.add_message(question)
    await send_text(update, context, answer)


async def personality_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Handling /talk command")
    context.user_data.clear()
    text = load_message('talk')
    await send_image(update, context, 'talk')
    await send_text(update, context, text)
    await send_text_buttons(update, context, "Выберите личность:", {
        'personality_cobain': 'Курт Кобейн 🎸',
        'personality_hawking': 'Стивен Хокинг 🔬',
        'personality_nietzsche': 'Фридрих Ницше 🧠',
        'personality_queen': 'Елизавета II 👑',
        'personality_tolkien': 'Джон Толкиен 📖',
        'start': 'Главное меню'
    })


async def personality_handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Handling personality selection")
    query = update.callback_query
    await query.answer()
    personality = query.data
    if personality == 'start':
        await start(update, context)
        return

    prompt = load_prompt(personality)
    chat_gpt.set_prompt(prompt)
    await send_text(update, context, f"Вы выбрали {personality.replace('personality_', '')}. Как я могу помочь?")
    context.user_data['current_personality'] = personality


async def personality_talk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Personality talk")
    user_message = update.message.text
    current_personality = context.user_data.get('current_personality')

    if not current_personality:
        await send_text(update, context, "Нет текущей личности для разговора.")
        return

    thinking_message = await send_text(update, context,
                                       f"{current_personality.replace('personality_', '')} думает над ответом...")
    response = await chat_gpt.add_message(user_message)
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=thinking_message.message_id)
    formatted_response = f"{current_personality.replace('personality_', '')}: {response}"
    await send_text(update, context, formatted_response)


async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Handling /quiz command")
    context.user_data.clear()
    text = load_message('quiz')
    await send_image(update, context, 'quiz')
    await send_text(update, context, text)
    prompt = load_prompt('quiz')
    chat_gpt.set_prompt(prompt)
    await send_text_buttons(update, context, "Выберите тему:", {
        'quiz_prog': 'Программирование',
        'quiz_math': 'Математика',
        'quiz_biology': 'Биология',
        'start': 'Главное меню'
    })


async def handle_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Handling quiz topic selection")
    query = update.callback_query
    await query.answer()
    topic = query.data.replace('quiz_', '')

    if topic == 'start':
        await start(update, context)
        return

    question = await chat_gpt.send_question("", f"Сгенерируй уникальный вопрос на русском языке на тему {topic}.")
    await send_text(update, context, f"Вопрос: {question}")
    context.user_data['current_topic'] = topic
    context.user_data['correct_answers'] = 0
    context.user_data['total_questions'] = 0


async def answer_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Handling quiz answer")
    user_answer = update.message.text
    current_topic = context.user_data.get('current_topic')
    correct_answers = context.user_data.get('correct_answers', 0)
    total_questions = context.user_data.get('total_questions', 0)

    if not current_topic:
        await send_text(update, context, "Нет текущего вопроса.")
        return

    thinking_message = await send_text(update, context, "Проверка ответа...")
    response = await chat_gpt.add_message(
        f"Проверь ответ на русском языке: {user_answer} ({current_topic}). "
        f"Ответь только в формате: 'Правильно!' или 'Неправильно! Правильный ответ - {{answer}}'."
    )
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=thinking_message.message_id)

    if "Правильно!" in response:
        correct_answers += 1
        await send_text(update, context, "Правильно!")
    else:
        correct_answer = response.split("Правильный ответ - ")[-1]
        await send_text(update, context, f"Неправильно! Правильный ответ - {correct_answer}")

    total_questions += 1

    context.user_data['correct_answers'] = correct_answers
    context.user_data['total_questions'] = total_questions

    next_question = await chat_gpt.send_question("",
                                                 f"Сгенерируй ещё один вопрос на русском языке на тему {current_topic}.")
    await send_text(update, context, f"Следующий вопрос: {next_question}")

    await send_text_buttons(update, context, f"Правильных ответов: {correct_answers}/{total_questions}", {
        'quiz_more': 'Ещё вопрос',
        'quiz_change': 'Сменить тему',
        'start': 'Закончить квиз'
    })


async def change_quiz_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await send_text(update, context, "Выберите новую тему для квиза:")
    await quiz(update, context)


async def translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    text = load_message('translate')
    await send_text(update, context, text)

    prompt = load_prompt('translate')
    chat_gpt.set_prompt(prompt)

    await send_text_buttons(update, context, "Выберите язык для перевода:", {
        'translate_ru_to_en': 'Русский → Английский',
        'translate_en_to_ru': 'Английский → Русский',
        'start': 'Главное меню'
    })


async def handle_translation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    query = update.callback_query
    await query.answer()
    language = query.data

    if language == 'start':
        await start(update, context)
        return

    context.user_data['current_language'] = language
    await send_text(update, context, f"Выбран язык: {language.replace('_', ' → ')}. Введите текст для перевода:")


async def translate_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_text = update.message.text
    current_language = context.user_data.get('current_language')
    if not current_language:
        await send_text(update, context, "Нет выбранного языка для перевода.")
        return

    thinking_message = await send_text(update, context, "Перевод текста...")

    response = await chat_gpt.add_message(f"{user_text} ({current_language})")

    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=thinking_message.message_id)

    await send_text(update, context, f"Перевод: {response}")

    await send_text_buttons(update, context, "Выберите действие:", {
        'translate_ru_to_en': 'Сменить язык на Русский → Английский',
        'translate_en_to_ru': 'Сменить язык на Английский → Русский',
        'start': 'Закончить перевод'
    })


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(update.message.text)
    if update.message.text.startswith("quiz_more"):
        await answer_quiz(update, context)
    else:
        await handle_conversation(update, context)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    if isinstance(update, Update) and update.callback_query:
        await update.callback_query.answer(text="Произошла ошибка. Попробуйте снова.", show_alert=True)
    elif isinstance(update, Update) and update.message:
        await update.message.reply_text("Произошла ошибка. Попробуйте снова.")


app.add_handler(CommandHandler('start', start))
app.add_handler(CommandHandler('random', random_fact))
app.add_handler(CommandHandler('gpt', question_chat_gpt))
app.add_handler(CommandHandler('talk', personality_menu))
app.add_handler(CommandHandler('quiz', quiz))
app.add_handler(CommandHandler('translate', translate))

app.add_handler(CallbackQueryHandler(personality_handle, pattern='^personality_.*'))
app.add_handler(CallbackQueryHandler(handle_quiz, pattern='^quiz_.*'))
app.add_handler(CallbackQueryHandler(handle_main_menu, pattern='^(start|random|gpt|talk|quiz|translate)$'))
app.add_handler(CallbackQueryHandler(handle_translation, pattern='^translate_.*'))
# Message handler filters
app.add_handler(MessageHandler(filters.TEXT, handle_message))
# Error handler
app.add_error_handler(error_handler)
# Start the bot
app.run_polling()
