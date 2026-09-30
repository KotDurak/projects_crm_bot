import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID") # <-- Добавили это

ITEMS_PER_PAGE = 10

PROJECTS = [
    "image_bot",
    "vk_flirt_bot",
    "tg_flirt_bot",
    "shira_neuro_bot"
]