import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from bot.config import OWNER_ID
from bot.services.database import db

router = Router()
log = logging.getLogger(__name__)


@router.message(Command("start"), StateFilter("*"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    uid = message.from_user.id
    from bot.handlers.admin import is_admin
    if not await is_admin(uid):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛍 Xarid qilish", callback_data="user_channels")]
        ])
        await message.answer(
            "Assalomu alaykum! 👋\n\n"
            "AutoSeller botiga xush kelibsiz!\n"
            "Kanallarimizdagi mahsulotlarni sotib olishingiz mumkin.",
            reply_markup=kb,
        )


@router.callback_query(F.data == "user_channels")
async def cb_user_channels(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    channels = await db.get_active_channels()
    if not channels:
        await callback.message.edit_text("Hozircha kanallar yo'q.")
        return await callback.answer()
    buttons = []
    for ch in channels:
        link = f"https://t.me/{ch['channel_id'].replace('-100', '')}"
        buttons.append([InlineKeyboardButton(text=f"📢 {ch['channel_name']}", url=link)])
    await callback.message.edit_text(
        "📢 Kanallarimiz:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await callback.answer()
