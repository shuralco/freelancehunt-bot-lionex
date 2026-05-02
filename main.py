"""
Freelancehunt monitor service.

Monitor-only режим: бот ТІЛЬКИ шле повідомлення про нові FH-проєкти у Telegram.
Updates (callback_query, message, business_*) ловить CRM-webhook на
https://crm.lionex.com.ua/api/telegram/webhook (інакше polling+webhook конфліктують).

Що робить цей сервіс:
  • опитує api.freelancehunt.com кожні 30 сек
  • upsert у локальну SQLite для дедупа
  • bot.send_message(...) у Telegram-чат
"""
import asyncio
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import settings
from database.storage import init_db
from services.monitor import start_monitoring
from services.cleaner import start_cleaner
from utils.logger import logger


async def main():
    await init_db()

    bot = Bot(
        token=settings.BOT_TOKEN.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    logger.info("Monitor service starting (no polling — webhook lives on CRM)...")

    monitor_task = asyncio.create_task(start_monitoring(bot))
    cleaner_task = asyncio.create_task(start_cleaner())

    try:
        await asyncio.gather(monitor_task, cleaner_task)
    finally:
        monitor_task.cancel()
        cleaner_task.cancel()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
