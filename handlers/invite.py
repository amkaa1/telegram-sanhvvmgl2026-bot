from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from loader import bot
from services.invite_tracker import get_personal_invite_link


router = Router()


@router.message(Command("invite"))
async def cmd_invite(message: Message) -> None:
    if message.from_user is None:
        return

    link = await get_personal_invite_link(bot, message.from_user.id)
    text = (
        "📨 <b>Таны урилгын хувийн линк</b>\n\n"
        f"{link}\n\n"
        "Энэ линкээр нэгдсэн бүх гишүүд таны урилгын тоонд тоологдоно."
    )
    await message.answer(text)

