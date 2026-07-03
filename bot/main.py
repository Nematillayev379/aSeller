import asyncio
import logging
import sys
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import BOT_TOKEN, OWNER_ID
from bot.services.database import db
from bot.services.product_api import product_api
from bot.services.scheduler import start_scheduler, stop_scheduler
from bot.middlewares.antiflood import AntiFloodMiddleware
from bot.handlers import admin, user


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        pass


def start_http_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()


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

    threading.Thread(target=start_http_server, daemon=True).start()
    log.info("HTTP server started on port %s", os.environ.get("PORT", 8080))

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
