from aiogram import Router
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import Message

from database.db import SessionLocal
from keyboards.menu import open_bot_private_keyboard
from keyboards.reply import (
    main_menu_keyboard,
)
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
        sent = await message.answer(
            "✅ Цэс нээгдлээ. Доорх товчийг ашиглана уу ✅",
            reply_markup=main_menu_keyboard(selective=True),
        )
        schedule_delete_message(
            message.bot,
            chat_id=sent.chat.id,
            message_id=sent.message_id,
            delay_seconds=60,
        )
        return
    await message.answer("✅ Цэс нээгдлээ ✅", reply_markup=main_menu_keyboard())
