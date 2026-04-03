from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from services.invite_tracker import get_personal_invite_link


router = Router()


@router.message(Command("invite"))
async def cmd_invite(message: Message) -> None:
    if message.from_user is None:
        return

    link = await get_personal_invite_link(message.bot, message.from_user.id)
    text = (
        "📨 <b>Таны invite холбоос</b>\n\n"
        f"{link}\n\n"
        "Хүн group-д орж ирсний дараа invite тоологдоно."
    )
    await message.answer(text)

