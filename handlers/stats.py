from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from analytics.stats import build_stats_text
from config import settings
from database.db import SessionLocal

router = Router()


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    if message.from_user is None or message.from_user.id not in settings.admin_ids:
        await message.answer("Энэ командыг зөвхөн админ ашиглана.")
        return
    async with SessionLocal() as session:  # type: AsyncSession
        text = await build_stats_text(session)
    await message.answer(text)
