from aiogram import Router
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardRemove

from database.db import SessionLocal
from keyboards.inline import group_target_menu_keyboard
from keyboards.menu import open_bot_private_keyboard
from services.temp_message_service import schedule_delete_message
from services.user_registry import has_private_started

router = Router()

@router.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    if message.from_user is None:
        return
    if message.chat.type in {ChatType.GROUP, ChatType.SUPERGROUP}:
        async with SessionLocal() as session:
            started = await has_private_started(session, message.from_user)
            await session.commit()
        if not started:
            sent = await message.answer(
                "🔒 Bot ашиглахын тулд эхлээд private chat дээр /start дарна уу 🔒",
                reply_markup=open_bot_private_keyboard(),
            )
            schedule_delete_message(
                message.bot,
                chat_id=sent.chat.id,
                message_id=sent.message_id,
                delay_seconds=15,
            )
            return
        target = message.reply_to_message.from_user if message.reply_to_message else None
        if target is None:
            sent = await message.reply(
                "⚠️ /menu ашиглахдаа тухайн хэрэглэгчийн мессеж дээр reply хийгээд ашиглана уу."
            )
            schedule_delete_message(
                message.bot,
                chat_id=sent.chat.id,
                message_id=sent.message_id,
                delay_seconds=12,
            )
            return
        if target.is_bot:
            sent = await message.reply("⚠️ Bot хэрэглэгч дээр энэ цэсийг ашиглах боломжгүй ⚠️")
            schedule_delete_message(
                message.bot,
                chat_id=sent.chat.id,
                message_id=sent.message_id,
                delay_seconds=12,
            )
            return
        sent = await message.reply(
            "✅ Түр цэс нээгдлээ. Доорх товчуудаас сонгоно уу ✅",
            reply_markup=group_target_menu_keyboard(target.id),
        )
        schedule_delete_message(
            message.bot,
            chat_id=sent.chat.id,
            message_id=sent.message_id,
            delay_seconds=25,
        )
        return
    await message.answer(
        "Group дээр /menu гэж бичээд ашиглах боломжтой .",
        reply_markup=ReplyKeyboardRemove(),
    )
