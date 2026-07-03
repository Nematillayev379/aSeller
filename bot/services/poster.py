import logging
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.config import OWNER_ID
from bot.services.database import db
from bot.services.template import template_builder

log = logging.getLogger(__name__)


class Poster:
    def __init__(self, bot: Bot):
        self.bot = bot

    def _buy_kb(self, ad_id: int = 0) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🛒 Buyurtma berish",
                url="https://t.me/rayimqulova111",
            )]
        ])

    async def post_product(self, product: dict) -> bool:
        channels = await db.get_active_channels()
        if not channels:
            log.warning("Faol kanallar yo'q")
            return False

        text = template_builder.build_scraped_ad_text(product)
        keyboard = self._buy_kb()

        posted = False
        for ch in channels:
            try:
                if product.get("image_url"):
                    await self.bot.send_photo(
                        chat_id=ch["channel_id"],
                        photo=product["image_url"],
                        caption=text,
                        parse_mode="HTML",
                        reply_markup=keyboard,
                    )
                else:
                    await self.bot.send_message(
                        chat_id=ch["channel_id"],
                        text=text,
                        parse_mode="HTML",
                        reply_markup=keyboard,
                    )
                posted = True
            except Exception as e:
                log.error("Post xatosi (%s): %s", ch["channel_id"], e)

        if posted:
            await db.add_ad(
                user_id=0,
                image_file_id=product.get("image_url", ""),
                title=product.get("title", ""),
                price=product.get("price", 0),
                description=product.get("source", ""),
                source=product.get("source", "auto"),
                external_id=product.get("external_id", ""),
                product_url=product.get("product_url", ""),
            )
        return posted

    async def post_ad_to_channels(self, ad: dict) -> int:
        channels = await db.get_active_channels()
        if not channels:
            return 0

        text = template_builder.build_ad_text(ad)
        keyboard = self._buy_kb(ad.get("id", 0))

        posted = 0
        for ch in channels:
            try:
                image = ad.get("image_file_id", "")
                if image:
                    await self.bot.send_photo(
                        chat_id=ch["channel_id"],
                        photo=image,
                        caption=text,
                        parse_mode="HTML",
                        reply_markup=keyboard,
                    )
                else:
                    await self.bot.send_message(
                        chat_id=ch["channel_id"],
                        text=text,
                        parse_mode="HTML",
                        reply_markup=keyboard,
                    )
                posted += 1
            except Exception as e:
                log.error("Post xatosi (%s): %s", ch["channel_id"], e)
        return posted


_poster: Poster | None = None


def get_poster(bot: Bot) -> Poster:
    global _poster
    if _poster is None:
        _poster = Poster(bot)
    return _poster
