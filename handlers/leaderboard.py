from html import escape

from aiogram import Router
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import SessionLocal
from database.models import User
from database.queries import get_top_users_by_invites, get_top_users_by_reputation
from utils.messaging import notice_dm_blocked, notice_dm_sent, safe_send_dm

router = Router()


async def _format_top_rep(session: AsyncSession) -> str:
    top_rep = await get_top_users_by_reputation(session, limit=10)
    lines: list[str] = ["⭐ <b>Reputation — топ 10</b>"]
    if not top_rep:
        lines.append("— Одоогоор өгөгдөл алга.")
        return "\n".join(lines)
    for i, u in enumerate(top_rep, start=1):
        label = escape(u.username) if u.username else str(u.telegram_id)
        lines.append(
            f"{i}. <a href=\"tg://user?id={u.telegram_id}\">{label}</a> "
            f"— 👍 {u.reputation_positive} / 👎 {u.reputation_negative}"
        )
    return "\n".join(lines)


async def _format_top_inv(session: AsyncSession) -> str:
    top_inv = await get_top_users_by_invites(session, limit=10)
    lines: list[str] = ["📨 <b>Урилга — топ 10</b>"]
    if not top_inv:
        lines.append("— Одоогоор өгөгдөл алга.")
        return "\n".join(lines)
    for i, u in enumerate(top_inv, start=1):
        label = escape(u.username) if u.username else str(u.telegram_id)
        lines.append(
            f"{i}. <a href=\"tg://user?id={u.telegram_id}\">{label}</a> "
            f"— {u.invites_count:,} урилга"
        )
    return "\n".join(lines)


async def _build_leaderboard_body(session: AsyncSession) -> str:
    rep = await _format_top_rep(session)
    inv = await _format_top_inv(session)
    return "🏆 <b>Leaderboard</b>\n\n" + rep + "\n\n" + inv


@router.message(Command("top", "leaderboard"))
async def cmd_top(message: Message) -> None:
    async with SessionLocal() as session:  # type: AsyncSession
        body = await _build_leaderboard_body(session)

    if message.from_user is None:
        return

    if message.chat.type == ChatType.PRIVATE:
        await message.answer(body)
        return

    sent = await safe_send_dm(
        message.bot,
        telegram_user_id=message.from_user.id,
        text=body,
    )
    if sent:
        await message.answer(notice_dm_sent())
        return

    async with SessionLocal() as session:  # type: AsyncSession
        top_rep = await get_top_users_by_reputation(session, limit=3)
        top_inv = await get_top_users_by_invites(session, limit=3)
    rep_lines = []
    for i, u in enumerate(top_rep, start=1):
        label = escape(u.username) if u.username else str(u.telegram_id)
        rep_lines.append(f"{i}. {label} — 👍{u.reputation_positive}")
    inv_lines = []
    for i, u in enumerate(top_inv, start=1):
        label = escape(u.username) if u.username else str(u.telegram_id)
        inv_lines.append(f"{i}. {label} — {u.invites_count}")
    extra = ""
    if rep_lines or inv_lines:
        extra = (
            "\n\n<b>Товч (топ 3)</b>\n"
            + ("⭐ " + "\n".join(rep_lines) + "\n\n" if rep_lines else "")
            + ("📨 " + "\n".join(inv_lines) if inv_lines else "")
        )
    await message.answer(f"{notice_dm_blocked()}{extra}")


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
