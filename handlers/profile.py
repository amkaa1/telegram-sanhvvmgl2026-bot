from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import SessionLocal
from database.queries import get_or_create_user
from services.reputation import get_trust_level, is_verified


router = Router()


@router.message(Command("profile"))
async def cmd_profile(message: Message) -> None:
    if message.from_user is None:
        return

    target = message.reply_to_message.from_user if message.reply_to_message else message.from_user

    async with SessionLocal() as session:  # type: AsyncSession
        user = await get_or_create_user(
            session,
            telegram_id=target.id,
            username=target.username,
            first_name=target.first_name,
            last_name=target.last_name,
        )

        level = get_trust_level(user.reputation_positive)
        verified_badge = "✔ Verified" if is_verified(user.reputation_positive) or user.verified else ""

        lines: list[str] = []
        lines.append(f"👤 Профайл: <a href=\"tg://user?id={target.id}\">{target.full_name}</a>")
        if target.username:
            lines.append(f"🔗 Username: @{target.username}")
        lines.append("")
        lines.append(f"⭐ Итгэлийн түвшин: <b>{level}</b>")
        lines.append(f"👍 Сайн: <b>{user.reputation_positive}</b>")
        lines.append(f"👎 Муу: <b>{user.reputation_negative}</b>")
        lines.append(f"📨 Урилга: <b>{user.invites_count}</b>")
        if verified_badge:
            lines.append(f"🔒 Статус: <b>{verified_badge}</b>")

        await message.answer("\n".join(lines))

