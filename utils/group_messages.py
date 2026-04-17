"""Optional group channel copy (Mongolian)."""

from aiogram import Bot
from aiogram.enums import ParseMode


GROUP_INTRO_TEXT = (
    "👋 Манай группт тавтай морил!\n\n"
    "Trust System, Invite System, Reward System-тэй bot ажиллаж байна.\n\n"
    "📌 Дэлгэрэнгүйг bot руу /start гэж бичээд үзээрэй."
)


async def send_group_intro_message(bot: Bot, chat_id: int) -> None:
    """Send the standard group intro message."""
    await bot.send_message(
        chat_id,
        GROUP_INTRO_TEXT,
        parse_mode=ParseMode.HTML,
    )
