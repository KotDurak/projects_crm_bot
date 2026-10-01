import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID") # <-- Добавили это

ITEMS_PER_PAGE = 10

PROJECTS = [
    "image_bot",
    "vk_flirt_bot",
    "tg_flirt_bot",
    "shira_neuro_bot"
]