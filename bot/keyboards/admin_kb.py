from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.config import OWNER_ID


def get_admin_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📦 Mahsulotlar", callback_data="admin_ads"),
            InlineKeyboardButton(text="🔄 Post qilish", callback_data="admin_post_now"),
        ],
        [
            InlineKeyboardButton(text="📢 Kanallar", callback_data="admin_channels"),
            InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats"),
        ],
        [
            InlineKeyboardButton(text="🛒 Buyurtmalar", callback_data="admin_orders"),
            InlineKeyboardButton(text="👥 Adminlar", callback_data="admin_users"),
        ],
    ])


def get_admin_ads_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Yangi qo'shish", callback_data="admin_add_ad"),
            InlineKeyboardButton(text="🔄 Post qilish", callback_data="admin_post_now"),
        ],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="admin_main")],
    ])


def get_admin_channels_kb(channels: list) -> InlineKeyboardMarkup:
    buttons = []
    for ch in channels:
        status = "✅" if ch["is_active"] else "❌"
        buttons.append([
            InlineKeyboardButton(text=f"{status} {ch['channel_name']}", callback_data=f"ch_toggle:{ch['channel_id']}"),
            InlineKeyboardButton(text="🗑", callback_data=f"ch_remove:{ch['channel_id']}"),
        ])
    buttons.append([InlineKeyboardButton(text="➕ Kanal qo'shish", callback_data="admin_add_channel")])
    buttons.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="admin_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_users_kb(users: list) -> InlineKeyboardMarkup:
    buttons = []
    for u in users:
        if u["user_id"] != OWNER_ID:
            buttons.append([
                InlineKeyboardButton(text=f"❌ {u['full_name']}", callback_data=f"adm_remove:{u['user_id']}"),
            ])
    buttons.append([InlineKeyboardButton(text="➕ Admin qo'shish", callback_data="admin_add_user")])
    buttons.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="admin_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="admin_main")],
    ])
