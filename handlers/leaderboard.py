from html import escape

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import SessionLocal
from database.models import User
from database.queries import get_top_users_by_invites, get_top_users_by_reputation

router = Router()


async def _format_top_rep(session: AsyncSession) -> str:
    top_rep = await get_top_users_by_reputation(session, limit=10)
    lines: list[str] = ["⭐ <b>Хамгийн найдвартай гишүүд</b>"]
    if not top_rep:
        lines.append("— Одоогоор өгөгдөл алга.")
        return "\n".join(lines)
    for i, u in enumerate(top_rep, start=1):
        label = escape(u.username) if u.username else str(u.telegram_id)
        lines.append(
            f"{i}. <a href=\"tg://user?id={u.telegram_id}\">{label}</a> "
            f"- 👍 {u.reputation_positive} / 👎 {u.reputation_negative}"
        )
    return "\n".join(lines)


async def _format_top_inv(session: AsyncSession) -> str:
    top_inv = await get_top_users_by_invites(session, limit=10)
    lines: list[str] = ["📨 <b>Урилгаар тэргүүлэгчид</b>"]
    if not top_inv:
        lines.append("— Одоогоор өгөгдөл алга.")
        return "\n".join(lines)
    for i, u in enumerate(top_inv, start=1):
        label = escape(u.username) if u.username else str(u.telegram_id)
        lines.append(
            f"{i}. <a href=\"tg://user?id={u.telegram_id}\">{label}</a> "
            f"- {u.invites_count:,} урилга"
        )
    return "\n".join(lines)


@router.message(Command("top", "leaderboard"))
async def cmd_top(message: Message) -> None:
    async with SessionLocal() as session:  # type: AsyncSession
        rep = await _format_top_rep(session)
        inv = await _format_top_inv(session)
    await message.answer(
        "🏆 <b> leaderboard </b>\n\n" + rep + "\n\n" + inv
    )


@router.message(Command("topinvite"))
async def cmd_top_invite(message: Message) -> None:
    async with SessionLocal() as session:  # type: AsyncSession
        text = await _format_top_inv(session)
    await message.answer(text)


@router.message(Command("topgood"))
async def cmd_top_good(message: Message) -> None:
    async with SessionLocal() as session:  # type: AsyncSession
        top = await get_top_users_by_reputation(session, limit=10)
    lines = ["👍 <b>Сайн үнэлгээтэй топ</b>"]
    if not top:
        lines.append("— Одоогоор өгөгдөл алга.")
    else:
        for i, u in enumerate(top, start=1):
            label = escape(u.username) if u.username else str(u.telegram_id)
            lines.append(
                f"{i}. <a href=\"tg://user?id={u.telegram_id}\">{label}</a> "
                f"- 👍 {u.reputation_positive}"
            )
    await message.answer("\n".join(lines))


@router.message(Command("topbad"))
async def cmd_top_bad(message: Message) -> None:
    async with SessionLocal() as session:  # type: AsyncSession
        res = await session.execute(
            select(User).order_by(User.reputation_negative.desc()).limit(10)
        )
        top = res.scalars().all()
    lines = ["👎 <b>Муу үнэлгээтэй топ</b>"]
    if not top:
        lines.append("— Одоогоор өгөгдөл алга.")
    else:
        for i, u in enumerate(top, start=1):
            label = escape(u.username) if u.username else str(u.telegram_id)
            lines.append(
                f"{i}. <a href=\"tg://user?id={u.telegram_id}\">{label}</a> "
                f"- 👎 {u.reputation_negative}"
            )
    await message.answer("\n".join(lines))
