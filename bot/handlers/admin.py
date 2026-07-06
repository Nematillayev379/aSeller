import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest

from bot.config import OWNER_ID
from bot.services.database import db
from bot.services.poster import get_poster
from bot.services.template import template_builder
from bot.keyboards.admin_kb import (
    get_admin_main_kb, get_admin_ads_kb, get_admin_channels_kb,
    get_admin_users_kb, get_back_kb,
)

router = Router()
log = logging.getLogger(__name__)


class FSM(StatesGroup):
    manual_photo = State()
    manual_title = State()
    manual_old_price = State()
    manual_new_price = State()
    manual_sizes = State()
    manual_colors = State()
    channel_id = State()
    channel_name = State()
    admin_user_id = State()


async def is_admin(user_id: int) -> bool:
    return user_id == OWNER_ID or await db.is_admin_user(user_id)


def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


async def safe_edit(message, text, **kwargs):
    try:
        await message.edit_text(text, **kwargs)
    except TelegramBadRequest:
        pass
    except Exception as e:
        log.warning("safe_edit: %s", e)


async def safe_answer(callback, text="", **kwargs):
    try:
        await callback.answer(text, **kwargs)
    except Exception:
        pass


@router.message(Command("start"), StateFilter("*"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    uid = message.from_user.id
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
        return
    await message.answer(
        f"Admin paneli 🛠\n\n"
        f"Siz: <b>{message.from_user.full_name}</b>\n"
        f"ID: <code>{uid}</code>",
        reply_markup=get_admin_main_kb(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "admin_main")
async def cb_admin_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    if not await is_admin(callback.from_user.id):
        return await safe_answer(callback, "Ruxsat yo'q!", show_alert=True)
    await safe_edit(
        callback.message,
        f"Admin paneli 🛠\n\n"
        f"Siz: <b>{callback.from_user.full_name}</b>\n"
        f"ID: <code>{callback.from_user.id}</code>",
        reply_markup=get_admin_main_kb(),
        parse_mode="HTML",
    )
    await safe_answer(callback)


@router.callback_query(F.data == "admin_ads")
async def cb_ads(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await safe_answer(callback, "Ruxsat yo'q!", show_alert=True)
    ads = await db.get_all_ads(limit=10)
    text = template_builder.build_ads_list(ads)
    await safe_edit(callback.message, text, reply_markup=get_admin_ads_kb(), parse_mode="HTML")
    await safe_answer(callback)


# === MANUAL PRODUCT POSTING ===

@router.callback_query(F.data == "admin_add_ad")
async def cb_add_ad(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return await safe_answer(callback, "Ruxsat yo'q!", show_alert=True)
    await state.set_state(FSM.manual_photo)
    await safe_edit(
        callback.message,
        "📸 <b>Mahsulot qo'shish</b>\n\n"
        "1/6 — Rasm yuboring:",
        parse_mode="HTML",
    )
    await safe_answer(callback)


@router.message(FSM.manual_photo, F.photo)
async def msg_photo(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    await state.update_data(image_file_id=message.photo[-1].file_id)
    await state.set_state(FSM.manual_title)
    await message.answer("📝 <b>2/6 — Nomini kiriting:</b>", parse_mode="HTML")


@router.message(FSM.manual_photo, F.text)
async def msg_photo_text(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    if message.text.lower() in ("bekor", "cancel"):
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_admin_main_kb())
        return
    await message.answer("📸 Faqat rasm yuboring!")


@router.message(FSM.manual_title, F.text)
async def msg_title(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    if message.text.lower() in ("bekor", "cancel"):
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_admin_main_kb())
        return
    await state.update_data(title=message.text.strip())
    await state.set_state(FSM.manual_old_price)
    await message.answer("💰 <b>3/6 — Eski narx (so'm):</b>", parse_mode="HTML")


@router.message(FSM.manual_old_price, F.text)
async def msg_old_price(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    if message.text.lower() in ("bekor", "cancel"):
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_admin_main_kb())
        return
    try:
        price = int(message.text.strip().replace(" ", "").replace(",", "").replace("so'm", ""))
    except ValueError:
        return await message.answer("⚠️ Faqat raqam kiriting:")
    await state.update_data(old_price=price)
    await state.set_state(FSM.manual_new_price)
    await message.answer("💸 <b>4/6 — Yangi narx (so'm):</b>", parse_mode="HTML")


@router.message(FSM.manual_new_price, F.text)
async def msg_new_price(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    if message.text.lower() in ("bekor", "cancel"):
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_admin_main_kb())
        return
    try:
        price = int(message.text.strip().replace(" ", "").replace(",", "").replace("so'm", ""))
    except ValueError:
        return await message.answer("⚠️ Faqat raqam kiriting:")
    await state.update_data(new_price=price)
    await state.set_state(FSM.manual_sizes)
    await message.answer(
        "📏 <b>5/6 — O'lchamlar:</b>\n"
        "<i>Masalan: S, M, L yoki 38, 39, 40</i>\n"
        "<i>Yo'q bo'lsa 'yo'q' deb yozing</i>",
        parse_mode="HTML",
    )


@router.message(FSM.manual_sizes, F.text)
async def msg_sizes(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    if message.text.lower() in ("bekor", "cancel"):
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_admin_main_kb())
        return
    sizes = message.text.strip() if message.text.lower() not in ("yo'q", "yoq") else ""
    await state.update_data(sizes=sizes)
    await state.set_state(FSM.manual_colors)
    await message.answer(
        "🎨 <b>6/6 — Ranglar:</b>\n"
        "<i>Masalan: Qora, Oq, Qizil</i>\n"
        "<i>Yo'q bo'lsa 'yo'q' deb yozing</i>",
        parse_mode="HTML",
    )


@router.message(FSM.manual_colors, F.text)
async def msg_colors(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    if message.text.lower() in ("bekor", "cancel"):
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_admin_main_kb())
        return
    colors = message.text.strip() if message.text.lower() not in ("yo'q", "yoq") else ""
    data = await state.get_data()

    ok = await db.add_ad(
        user_id=message.from_user.id,
        image_file_id=data.get("image_file_id", ""),
        title=data.get("title", ""),
        price=data.get("new_price", 0),
        description=f"old:{data.get('old_price', 0)}|sizes:{data.get('sizes', '')}|colors:{data.get('colors', '')}",
    )
    await state.clear()

    if ok:
        await message.answer(
            f"✅ Mahsulot saqlandi!\n\n"
            f"📝 {data.get('title', '')}\n"
            f"💰 {data.get('old_price', 0):,} → {data.get('new_price', 0):,} so'm\n"
            f"📏 {data.get('sizes', "Yo'q")}\n"
            f"🎨 {data.get('colors', "Yo'q")}\n\n"
            f"Kanalga joylash uchun '🔄 Post qilish' bosing.",
            reply_markup=get_admin_main_kb(),
            parse_mode="HTML",
        )
    else:
        await message.answer("❌ Xatolik!", reply_markup=get_admin_main_kb())


@router.callback_query(F.data == "admin_post_now")
async def cb_post_now(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await safe_answer(callback, "Ruxsat yo'q!", show_alert=True)

    channels = await db.get_active_channels()
    if not channels:
        await safe_edit(callback.message, "📢 Kanal qo'shilmagan!", reply_markup=get_admin_main_kb())
        return await safe_answer(callback)

    unposted = await db.get_unposted_ads(limit=5)
    if not unposted:
        await safe_edit(callback.message, "📭 Joylanmagan mahsulotlar yo'q.", reply_markup=get_admin_main_kb())
        return await safe_answer(callback)

    poster = get_poster(callback.bot)
    posted = 0
    for ad in unposted:
        ad_dict = dict(ad)
        ok = await poster.post_ad_to_channels(ad_dict)
        if ok:
            await db.mark_ad_posted(ad_dict["id"])
            posted += 1

    await safe_edit(callback.message, f"✅ {posted} ta mahsulot kanalga joylandi!", reply_markup=get_admin_main_kb())
    await safe_answer(callback)


# === CHANNELS ===

@router.callback_query(F.data == "admin_channels")
async def cb_channels(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await safe_answer(callback, "Ruxsat yo'q!", show_alert=True)
    channels = await db.get_all_channels()
    text = template_builder.build_channels_list(channels)
    await safe_edit(callback.message, text, reply_markup=get_admin_channels_kb(channels))
    await safe_answer(callback)


@router.callback_query(F.data == "admin_add_channel")
async def cb_add_channel(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return await safe_answer(callback, "Ruxsat yo'q!", show_alert=True)
    await state.set_state(FSM.channel_id)
    await safe_edit(
        callback.message,
        "📢 Kanal ID kiriting:\n<code>-1001234567890</code>\n\nBotni kanalga admin qiling!",
        parse_mode="HTML",
    )
    await safe_answer(callback)


@router.message(FSM.channel_id, F.text)
async def msg_channel_id(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    cid = message.text.strip()
    if not cid.startswith("-100"):
        return await message.answer("⚠️ ID <code>-100</code> bilan boshlanishi kerak.", parse_mode="HTML")
    await state.update_data(channel_id=cid)
    await state.set_state(FSM.channel_name)
    await message.answer("📝 Kanal nomini kiriting:")


@router.message(FSM.channel_name, F.text)
async def msg_channel_name(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    data = await state.get_data()
    await db.add_channel(data.get("channel_id", ""), message.text.strip())
    await state.clear()
    await message.answer("✅ Kanal qo'shildi!", reply_markup=get_admin_main_kb())


@router.callback_query(F.data.startswith("ch_toggle:"))
async def cb_ch_toggle(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await safe_answer(callback, "Ruxsat yo'q!", show_alert=True)
    cid = callback.data.split(":", 1)[1]
    await db.toggle_channel(cid)
    channels = await db.get_all_channels()
    text = template_builder.build_channels_list(channels)
    await safe_edit(callback.message, text, reply_markup=get_admin_channels_kb(channels))
    await safe_answer(callback, "Holat o'zgartirildi!")


@router.callback_query(F.data.startswith("ch_remove:"))
async def cb_ch_remove(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await safe_answer(callback, "Ruxsat yo'q!", show_alert=True)
    cid = callback.data.split(":", 1)[1]
    await db.remove_channel(cid)
    channels = await db.get_all_channels()
    text = template_builder.build_channels_list(channels)
    await safe_edit(callback.message, text, reply_markup=get_admin_channels_kb(channels))
    await safe_answer(callback, "Kanal o'chirildi!")


# === STATS, ORDERS, USERS ===

@router.callback_query(F.data == "admin_stats")
async def cb_stats(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await safe_answer(callback, "Ruxsat yo'q!", show_alert=True)
    ad_stats = await db.get_ad_stats()
    order_stats = await db.get_order_stats()
    channels = await db.get_active_channels()
    text = template_builder.build_stats_message(ad_stats, order_stats, channels)
    await safe_edit(callback.message, text, reply_markup=get_back_kb(), parse_mode="HTML")
    await safe_answer(callback)


@router.callback_query(F.data == "admin_orders")
async def cb_orders(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await safe_answer(callback, "Ruxsat yo'q!", show_alert=True)
    orders = await db.get_all_orders(limit=10)
    text = template_builder.build_orders_list(orders)
    kb = get_back_kb()
    if orders:
        for o in orders:
            if o["status"] == "pending":
                kb.inline_keyboard.insert(0, [
                    InlineKeyboardButton(text=f"✅ #{o['id']}", callback_data=f"accept_order:{o['id']}"),
                    InlineKeyboardButton(text=f"❌ #{o['id']}", callback_data=f"reject_order:{o['id']}"),
                ])
    await safe_edit(callback.message, text, reply_markup=kb, parse_mode="HTML")
    await safe_answer(callback)


@router.callback_query(F.data == "admin_users")
async def cb_users(callback: CallbackQuery):
    if not is_owner(callback.from_user.id):
        return await safe_answer(callback, "Faqat owner!", show_alert=True)
    users = await db.get_all_admin_users()
    text = template_builder.build_admin_users_list(users)
    await safe_edit(callback.message, text, reply_markup=get_admin_users_kb(users), parse_mode="HTML")
    await safe_answer(callback)


@router.callback_query(F.data == "admin_add_user")
async def cb_add_user(callback: CallbackQuery, state: FSMContext):
    if not is_owner(callback.from_user.id):
        return await safe_answer(callback, "Faqat owner!", show_alert=True)
    await state.set_state(FSM.admin_user_id)
    await safe_edit(callback.message, "👤 Admin ID kiriting:")
    await safe_answer(callback)


@router.message(FSM.admin_user_id, F.text)
async def msg_admin_user(message: Message, state: FSMContext):
    if not is_owner(message.from_user.id):
        return
    try:
        uid = int(message.text.strip())
    except ValueError:
        return await message.answer("⚠️ Faqat raqam kiriting.")
    await db.add_admin_user(uid, "", f"User {uid}")
    await state.clear()
    await message.answer(f"✅ User <code>{uid}</code> admin qilindi!", reply_markup=get_admin_main_kb(), parse_mode="HTML")


@router.callback_query(F.data.startswith("adm_remove:"))
async def cb_remove_admin(callback: CallbackQuery):
    if not is_owner(callback.from_user.id):
        return await safe_answer(callback, "Faqat owner!", show_alert=True)
    uid = int(callback.data.split(":")[1])
    if uid == OWNER_ID:
        return await safe_answer(callback, "Owner o'zini o'chira olmaydi!", show_alert=True)
    await db.remove_admin_user(uid)
    users = await db.get_all_admin_users()
    text = template_builder.build_admin_users_list(users)
    await safe_edit(callback.message, text, reply_markup=get_admin_users_kb(users), parse_mode="HTML")
    await safe_answer(callback, "Admin o'chirildi!")


@router.callback_query(F.data.startswith("accept_order:"))
async def cb_accept_order(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await safe_answer(callback, "Ruxsat yo'q!", show_alert=True)
    oid = int(callback.data.split(":")[1])
    await db.update_order_status(oid, "completed")
    await safe_answer(callback, "✅ Qabul qilindi!")


@router.callback_query(F.data.startswith("reject_order:"))
async def cb_reject_order(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await safe_answer(callback, "Ruxsat yo'q!", show_alert=True)
    oid = int(callback.data.split(":")[1])
    await db.update_order_status(oid, "rejected")
    await safe_answer(callback, "❌ Rad etildi!")
