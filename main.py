import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from database import Database
from handlers import projects, sources

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


async def main():
    await Database.init()
    print("✅ База данных инициализирована")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(projects.router)
    dp.include_router(sources.router)

    print("🚀 Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())