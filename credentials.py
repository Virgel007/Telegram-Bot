from dotenv import load_dotenv
import os

load_dotenv()

ChatGPT_TOKEN = os.getenv('CHATGPT_TOKEN')
BOT_TOKEN = os.getenv('TELEGRAM_TOKEN')
