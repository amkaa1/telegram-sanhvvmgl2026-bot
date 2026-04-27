from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardRemove

from database.db import SessionLocal
from keyboards.menu import open_bot_private_keyboard
from keyboards.reply import REPLY_BTN_MENU, main_menu_keyboard
from services.temp_message_service import schedule_delete_message
from services.user_registry import has_private_started
from utils.logger import logger

router = Router()


async def handle_menu_request(message: Message) -> None:
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

        if message.reply_to_message and message.reply_to_message.from_user is None:
            sent = await message.reply("⚠️ Энэ хэрэглэгч дээр үйлдэл хийх боломжгүй.")
            schedule_delete_message(
                message.bot,
                chat_id=sent.chat.id,
                message_id=sent.message_id,
                delay_seconds=5,
            )
            return

        target = message.reply_to_message.from_user if message.reply_to_message else None
        if target and target.is_bot:
            sent = await message.reply("⚠️ Энэ хэрэглэгч дээр үйлдэл хийх боломжгүй.")
            schedule_delete_message(
                message.bot,
                chat_id=sent.chat.id,
                message_id=sent.message_id,
                delay_seconds=5,
            )
            return
        try:
            sent = await message.reply(
                "✅ Menu нээгдлээ үйлдлээ сонгоно уу.",
                reply_markup=main_menu_keyboard(selective=True),
            )
            schedule_delete_message(
                message.bot,
                chat_id=sent.chat.id,
                message_id=sent.message_id,
                delay_seconds=10,
            )
        except Exception:
            logger.exception("menu open failed actor_id=%s", message.from_user.id)
            sent = await message.reply("⚠️ Алдаа гарлаа. Дахин оролдоно уу.")
            schedule_delete_message(
                message.bot,
                chat_id=sent.chat.id,
                message_id=sent.message_id,
                delay_seconds=5,
            )
        return
    await message.answer(
        "Group дээр /menu гэж бичээд ашиглах боломжтой .",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    await handle_menu_request(message)


@router.message(
    F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}),
    F.text == REPLY_BTN_MENU,
)
async def menu_button(message: Message) -> None:
    await handle_menu_request(message)
