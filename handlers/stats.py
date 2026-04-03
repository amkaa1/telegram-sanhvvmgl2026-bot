from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from analytics.stats_formatter import format_stats
from config import settings
from database.db import session_scope
from services.stats_service import build_stats

router = Router()


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    if message.from_user is None or message.from_user.id not in settings.admin_ids:
        await message.answer("Энэ командыг зөвхөн админ ашиглана.")
        return
    async with session_scope() as session:
        data = await build_stats(session)
    await message.answer(format_stats(data))
