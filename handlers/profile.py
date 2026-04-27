from __future__ import annotations

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from database.db import SessionLocal
from database.queries import get_or_create_user, get_user_by_telegram_id
from keyboards.menu import open_bot_private_keyboard
from keyboards.reply import REPLY_BTN_PROFILE
from services.profile_service import format_profile_text
from services.temp_message_service import schedule_delete_message, send_temp_message
from services.user_registry import ensure_user_registered, has_private_started
from utils.logger import logger
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
    F.text == REPLY_BTN_PROFILE,
)
async def menu_profile(message: Message) -> None:
    if message.from_user is None:
        return
    if not await _ensure_group_activation(message):
        return
    target_tg = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    if target_tg is None or target_tg.is_bot:
        await send_temp_message(message, "⚠️ Энэ хэрэглэгч дээр үйлдэл хийх боломжгүй.", ttl_seconds=10)
        return
    async with SessionLocal() as session:
        await ensure_user_registered(session, message.from_user)
        target_user = await get_or_create_user(
            session,
            telegram_id=target_tg.id,
            username=target_tg.username,
            first_name=target_tg.first_name,
            last_name=target_tg.last_name,
        )
        profile_text = await format_profile_text(session, target_user)
        await session.commit()
    sent_msg = await message.answer(profile_text)
    schedule_delete_message(
        message.bot,
        chat_id=sent_msg.chat.id,
        message_id=sent_msg.message_id,
        delay_seconds=30 if message.reply_to_message else 5,
    )


@router.message(
    F.chat.type == ChatType.PRIVATE,
    F.text == REPLY_BTN_PROFILE,
)
async def private_stale_menu_profile(message: Message) -> None:
    await message.answer(
        "⚠️ Энэ товч хуучирсан байна. /profile эсвэл /profile @username ашиглана уу ⚠️",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.callback_query(F.data.regexp(r"^(profile:view|menu:profile):\d+$"))
async def inline_profile_callback(call: CallbackQuery) -> None:
    if call.from_user is None or call.data is None or call.message is None:
        return
    try:
        parts = call.data.split(":")
        if len(parts) == 3 and parts[0] == "menu":
            raw_target_id = parts[2]
        elif len(parts) == 3 and parts[0] == "profile":
            raw_target_id = parts[2]
        else:
            await call.answer("⚠️ Энэ үйлдэл хүчингүй байна.", show_alert=True)
            return
        if not raw_target_id.isdigit():
            await call.answer("⚠️ Энэ үйлдэл хүчингүй байна.", show_alert=True)
            return
        target_id = int(raw_target_id)
        if target_id <= 0:
            await call.answer("⚠️ Энэ үйлдэл хүчингүй байна.", show_alert=True)
            return

        async with SessionLocal() as session:
            await ensure_user_registered(session, call.from_user)
            target_db = await get_user_by_telegram_id(session, target_id)
            if target_db and target_db.is_bot:
                await session.commit()
                await call.answer("⚠️ Энэ хэрэглэгч дээр үйлдэл хийх боломжгүй.", show_alert=True)
                return

            target_user = target_db
            if target_user is None and call.message.chat.type in {ChatType.GROUP, ChatType.SUPERGROUP}:
                try:
                    member = await call.bot.get_chat_member(call.message.chat.id, target_id)
                    target_user = await get_or_create_user(
                        session,
                        telegram_id=member.user.id,
                        username=member.user.username,
                        first_name=member.user.first_name,
                        last_name=member.user.last_name,
                    )
                except Exception:
                    target_user = None
            if target_user is None:
                await session.commit()
                await call.answer("⚠️ Энэ хэрэглэгч дээр үйлдэл хийх боломжгүй.", show_alert=True)
                return
            profile_text = await format_profile_text(session, target_user)
            await session.commit()

        await call.answer("✅ Профайл бэлэн.")
        sent_msg = await call.message.answer(profile_text)
        schedule_delete_message(
            call.bot,
            chat_id=sent_msg.chat.id,
            message_id=sent_msg.message_id,
            delay_seconds=25,
        )
    except Exception:
        logger.exception("menu profile callback failed data=%s actor_id=%s", call.data, call.from_user.id)
        await call.answer("⚠️ Алдаа гарлаа. Дахин оролдоно уу.", show_alert=True)
