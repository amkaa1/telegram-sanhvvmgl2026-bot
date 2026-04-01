from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import SessionLocal
from database.queries import get_top_users_by_invites, get_top_users_by_reputation


router = Router()


@router.message(Command("top"))
async def cmd_top(message: Message) -> None:
    async with SessionLocal() as session:  # type: AsyncSession
        top_rep = await get_top_users_by_reputation(session, limit=10)
        top_inv = await get_top_users_by_invites(session, limit=10)

    lines: list[str] = []
    lines.append("🏆 <b>Лидерүүдийн хүснэгт</b>")
    lines.append("")

    if top_rep:
        lines.append("⭐ <b>Итгэлцлээр тэргүүлэгчид</b>")
        for i, u in enumerate(top_rep, start=1):
            lines.append(
                f"{i}. <a href=\"tg://user?id={u.telegram_id}\">{u.username or u.telegram_id}</a> "
                f"- 👍 {u.reputation_positive} / 👎 {u.reputation_negative}"
            )
        lines.append("")

    if top_inv:
        lines.append("📨 <b>Урилгаар тэргүүлэгчид</b>")
        for i, u in enumerate(top_inv, start=1):
            lines.append(
                f"{i}. <a href=\"tg://user?id={u.telegram_id}\">{u.username or u.telegram_id}</a> "
                f"- {u.invites_count} урилга"
            )

    await message.answer("\n".join(lines))

