from __future__ import annotations

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import Message

from database.db import SessionLocal
from database.queries import get_or_create_user
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
        await message.answer(profile_text)
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


@router.message(F.text == "👤 Profile")
async def menu_profile(message: Message) -> None:
    pseudo = message.model_copy(update={"text": "/profile"})
    await cmd_profile(pseudo)
