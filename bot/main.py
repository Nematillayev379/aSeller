import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import BOT_TOKEN, OWNER_ID
from bot.services.database import db
from bot.services.product_api import product_api
from bot.services.scheduler import start_scheduler, stop_scheduler
from bot.middlewares.antiflood import AntiFloodMiddleware
from bot.handlers import admin, user


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
    )
    log = logging.getLogger("bot")

    if not BOT_TOKEN:
        log.error("BOT_TOKEN topilmadi!")
        return

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    dp.message.middleware(AntiFloodMiddleware())
    dp.callback_query.middleware(AntiFloodMiddleware())

    dp.include_routers(admin.router, user.router)

    await db.connect()
    await db.set_setting("owner_id", str(OWNER_ID))

    log.info("Bot ishga tushdi! Owner ID: %s", OWNER_ID)

    await start_scheduler(bot)

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await stop_scheduler()
        await product_api.close()
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
