from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database.db import SessionLocal
from services.reputation import rate_user


router = Router()


async def _extract_target_from_message(message: Message):
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user
    if message.entities:
        for ent in message.entities:
            if ent.type == "mention":
                username = message.text[ent.offset + 1 : ent.offset + ent.length]
                # Telegram username mention; we cannot resolve to user without extra API.
                # Тиймээс үнэлгээг зөвхөн reply хэлбэрээр ашиглахыг зөвлөе.
    return None


@router.message(Command("good"))
async def cmd_good(message: Message) -> None:
    if message.from_user is None:
        return
    target = await _extract_target_from_message(message)
    if target is None:
        await message.answer(
            "👍 Сайн үнэлгээ өгөхийн тулд тухайн гишүүний мессеж дээр reply хийгээд /good гэж бичнэ үү."
        )
        return

    async with SessionLocal() as session:
        ok, text = await rate_user(session, message.from_user, target, positive=True)
        await message.answer(text)


@router.message(Command("bad"))
async def cmd_bad(message: Message) -> None:
    if message.from_user is None:
        return
    target = await _extract_target_from_message(message)
    if target is None:
        await message.answer(
            "👎 Муу үнэлгээ өгөхийн тулд тухайн гишүүний мессеж дээр reply хийгээд /bad гэж бичнэ үү."
        )
        return

    async with SessionLocal() as session:
        ok, text = await rate_user(session, message.from_user, target, positive=False)
        await message.answer(text)

