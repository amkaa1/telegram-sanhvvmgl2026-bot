from aiogram import Router
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardRemove

from services.invite_tracker import get_personal_invite_link
from utils.messaging import notice_dm_blocked, notice_dm_sent, safe_send_dm

router = Router()


@router.message(Command("invite"))
async def cmd_invite(message: Message) -> None:
    if message.from_user is None:
        return

    link = await get_personal_invite_link(message.bot, message.from_user.id)
    detail = (
        "📨 <b>Таны Invite Link</b>\n\n"
        f"{link}\n\n"
        "Таны Invite хийсэн хүн Group-д нэгдсэний дараа урилга тоологдоно."
    )

    if message.chat.type == ChatType.PRIVATE:
        await message.answer(detail, reply_markup=ReplyKeyboardRemove())
        return

    sent = await safe_send_dm(
        message.bot,
        telegram_user_id=message.from_user.id,
        text=detail,
    )
    if sent:
        await message.answer(notice_dm_sent())
        return

    await message.answer(
        f"{notice_dm_blocked()}\n\n"
        f"📨 Урилгын линк:\n{link}"
    )
