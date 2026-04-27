from __future__ import annotations

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from database.db import SessionLocal
from database.queries import get_or_create_user, get_user_by_telegram_id
from keyboards.menu import open_bot_private_keyboard
from services.profile_service import format_profile_text
from services.temp_message_service import schedule_delete_message, send_temp_message
from services.user_registry import ensure_user_registered, has_private_started
from utils.messaging import safe_send_dm
from utils.target_user import resolve_profile_target

router = Router()

async def _ensure_group_activation(message: Message) -> bool:
    if message.from_user is None:
        return False
    if message.chat.type not in {ChatType.GROUP, ChatType.SUPERGROUP}:
        return True
    async with SessionLocal() as session:
        ok = await has_private_started(session, message.from_user)
        await session.commit()
    if ok:
        return True
    await send_temp_message(
        message,
        "🔒 Bot ашиглахын тулд эхлээд private chat дээр /start дарна уу 🔒",
        ttl_seconds=15,
        reply_markup=open_bot_private_keyboard(),
    )
    return False


@router.message(Command("profile"))
async def cmd_profile(message: Message) -> None:
    if message.from_user is None:
        return

    if not await _ensure_group_activation(message):
        return

    target_tg, err = await resolve_profile_target(message)
    if err:
        if message.chat.type in {ChatType.GROUP, ChatType.SUPERGROUP}:
            await send_temp_message(message, err, ttl_seconds=10)
        else:
            await message.answer(err)
        return
    if target_tg is None:
        await message.answer("⚠️ Энэ хэрэглэгчийг одоогоор таньж чадсангүй ⚠️")
        return

    async with SessionLocal() as session:
        await ensure_user_registered(session, message.from_user)
        user = await get_or_create_user(
            session,
            telegram_id=target_tg.id,
            username=target_tg.username,
            first_name=target_tg.first_name,
            last_name=target_tg.last_name,
        )
        profile_text = await format_profile_text(session, user)
        await session.commit()

    if message.chat.type == ChatType.PRIVATE:
        await message.answer(profile_text, reply_markup=ReplyKeyboardRemove())
        return

    if message.from_user.id == target_tg.id:
        sent = await safe_send_dm(
            message.bot,
            telegram_user_id=message.from_user.id,
            text=profile_text,
        )
        if sent:
            await send_temp_message(
                message,
                "👤 Өөрийн профайлыг DM рүү илгээлээ 👤",
                ttl_seconds=10,
            )
        else:
            await send_temp_message(
                message,
                "⚠️ DM рүү илгээж чадсангүй. Private chat дээр /start дарна уу ⚠️",
                ttl_seconds=10,
            )
        return

    if message.reply_to_message:
        sent_msg = await message.answer(profile_text)
        schedule_delete_message(
            message.bot,
            chat_id=sent_msg.chat.id,
            message_id=sent_msg.message_id,
            delay_seconds=30,
        )
        return
    sent_msg = await message.answer(profile_text)
    schedule_delete_message(
        message.bot,
        chat_id=sent_msg.chat.id,
        message_id=sent_msg.message_id,
        delay_seconds=30,
    )


@router.message(
    F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}),
    F.text.in_({"👤 Profile"}),
)
async def menu_profile(message: Message) -> None:
    await send_temp_message(
        message,
        "⚠️ Хуучин keyboard хүчингүй болсон. Хэрэглэгчийн мессеж дээр reply хийгээд /menu ашиглана уу ⚠️",
        ttl_seconds=10,
    )


@router.message(
    F.chat.type == ChatType.PRIVATE,
    F.text.in_({"👤 Profile"}),
)
async def private_stale_menu_profile(message: Message) -> None:
    await message.answer(
        "⚠️ Энэ товч хуучирсан байна. /profile эсвэл /profile @username ашиглана уу ⚠️",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.callback_query(F.data.regexp(r"^profile:view:\d+$"))
async def inline_profile_callback(call: CallbackQuery) -> None:
    if call.from_user is None or call.data is None or call.message is None:
        return
    parts = call.data.split(":")
    if len(parts) != 3 or not parts[2].isdigit():
        await call.answer("⚠️ Буруу callback формат ⚠️", show_alert=True)
        return
    target_id = int(parts[2])
    if target_id <= 0:
        await call.answer("⚠️ Хэрэглэгчийн ID буруу байна ⚠️", show_alert=True)
        return

    async with SessionLocal() as session:
        await ensure_user_registered(session, call.from_user)
        target_db = await get_user_by_telegram_id(session, target_id)
        if target_db and target_db.is_bot:
            await session.commit()
            await call.answer("⚠️ Bot-ын профайл харах боломжгүй ⚠️", show_alert=True)
            return
        try:
            target_tg = await call.bot.get_chat(target_id)
        except Exception:
            target_tg = None
        if target_tg is not None and getattr(target_tg, "is_bot", False):
            await session.commit()
            await call.answer("⚠️ Bot-ын профайл харах боломжгүй ⚠️", show_alert=True)
            return
        if target_tg is None and target_db is None:
            await session.commit()
            await call.answer("⚠️ Энэ хэрэглэгчийг одоогоор таньж чадсангүй ⚠️", show_alert=True)
            return

        target_user = target_db
        if target_user is None and target_tg is not None:
            target_user = await get_or_create_user(
                session,
                telegram_id=int(target_tg.id),
                username=getattr(target_tg, "username", None),
                first_name=getattr(target_tg, "first_name", None),
                last_name=getattr(target_tg, "last_name", None),
            )
        if target_user is None:
            await session.commit()
            await call.answer("⚠️ Энэ хэрэглэгчийг одоогоор таньж чадсангүй ⚠️", show_alert=True)
            return
        profile_text = await format_profile_text(session, target_user)
        await session.commit()

    await call.answer("✅ Профайл бэлэн ✅")
    if call.message.chat.type == ChatType.PRIVATE or target_id == call.from_user.id:
        sent = await safe_send_dm(
            call.bot,
            telegram_user_id=call.from_user.id,
            text=profile_text,
        )
        if not sent and call.message.chat.type in {ChatType.GROUP, ChatType.SUPERGROUP}:
            await send_temp_message(
                call.message,
                "⚠️ DM руу илгээж чадсангүй. Private chat дээр /start дарна уу ⚠️",
                ttl_seconds=10,
            )
        elif call.message.chat.type in {ChatType.GROUP, ChatType.SUPERGROUP}:
            await send_temp_message(
                call.message,
                "👤 Профайлыг DM рүү илгээлээ 👤",
                ttl_seconds=10,
            )
        return

    sent_msg = await call.message.answer(profile_text)
    schedule_delete_message(
        call.bot,
        chat_id=sent_msg.chat.id,
        message_id=sent_msg.message_id,
        delay_seconds=25,
    )
