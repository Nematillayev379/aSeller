import logging
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from bot.services.database import db
from bot.services.product_api import product_api
from bot.services.poster import get_poster

log = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


async def auto_fetch_and_post(bot: Bot):
    try:
        log.info("Avtomatik mahsulot olish boshlandi...")

        products = await product_api.fetch_random_products(count=3)
        if not products:
            log.warning("Mahsulotlar topilmadi")
            return

        poster = get_poster(bot)
        posted = 0
        for p in products:
            ok = await poster.post_product(p)
            if ok:
                posted += 1

        log.info("Avtomatik post: %d/%d ta mahsulot joylandi", posted, len(products))
    except Exception as e:
        log.error("Avtomatik post xatosi: %s", e)


async def start_scheduler(bot: Bot):
    interval_str = await db.get_setting("posting_interval")
    interval_minutes = int(interval_str) if interval_str else 60

    scheduler.add_job(
        auto_fetch_and_post,
        trigger=IntervalTrigger(minutes=interval_minutes),
        args=[bot],
        id="auto_poster",
        replace_existing=True,
    )
    scheduler.start()
    log.info("Scheduler: har %d daqiqada avtomatik post", interval_minutes)


async def restart_scheduler(bot: Bot):
    if scheduler.running:
        scheduler.shutdown(wait=False)
    await start_scheduler(bot)


async def stop_scheduler():
    try:
        if scheduler.running:
            scheduler.shutdown(wait=False)
    except Exception:
        pass
