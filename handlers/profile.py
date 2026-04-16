from __future__ import annotations

from html import escape

from aiogram import Router
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import SessionLocal
from database.queries import get_or_create_user
from services.reputation import get_trust_level
from utils.messaging import notice_dm_blocked, notice_dm_sent, safe_send_dm
from utils.target_user import resolve_profile_target

router = Router()


def _format_profile_detail(
    *,
    display_name: str,
    username: str | None,
    level: str,
    rep_pos: int,
    rep_neg: int,
    invites: int,
) -> str:
    uname = f"@{escape(username)}" if username else "—"
    sep = "━━━━━━━━━━━━━━"
    return "\n".join(
        [
            sep,
            f"👤 {escape(display_name)}",
            f"🔗 {uname}",
            sep,
            f"Trust: <b>{escape(level)}</b>",
            f"👍 {rep_pos} · 👎 {rep_neg}",
            f"📨 Урилга: {invites}",
            sep,
        ]
    )


def _format_profile_compact_line(
    *,
    display_name: str,
    username: str | None,
    level: str,
    rep_pos: int,
    rep_neg: int,
) -> str:
    who = f"@{escape(username)}" if username else escape(display_name)
    return (
        f"👤 {who} · Trust <b>{escape(level)}</b> · 👍{rep_pos} 👎{rep_neg}"
    )


@router.message(Command("profile"))
async def cmd_profile(message: Message) -> None:
    if message.from_user is None:
        return

    target_tg, err = await resolve_profile_target(message)
    if err:
        await message.answer(err)
        return
    if target_tg is None:
        await message.answer("Хэрэглэгч олдсонгүй.")
        return

    display_name = (
        " ".join(
            filter(
                None,
                [getattr(target_tg, "first_name", None), getattr(target_tg, "last_name", None)],
            )
        ).strip()
        or getattr(target_tg, "title", None)
        or (f"@{target_tg.username}" if target_tg.username else str(target_tg.id))
    )

    async with SessionLocal() as session:  # type: AsyncSession
        user = await get_or_create_user(
            session,
            telegram_id=target_tg.id,
            username=target_tg.username,
            first_name=target_tg.first_name,
            last_name=target_tg.last_name,
        )
        await session.commit()

    level = get_trust_level(user.reputation_positive)
    if user.verified and level != "Verified":
        level = "Verified"

    detail = _format_profile_detail(
        display_name=display_name,
        username=target_tg.username,
        level=level,
        rep_pos=user.reputation_positive,
        rep_neg=user.reputation_negative,
        invites=user.invites_count,
    )

    if message.chat.type == ChatType.PRIVATE:
        await message.answer(detail)
        return

    compact = _format_profile_compact_line(
        display_name=display_name,
        username=target_tg.username,
        level=level,
        rep_pos=user.reputation_positive,
        rep_neg=user.reputation_negative,
    )

    if message.from_user.id == target_tg.id:
        sent = await safe_send_dm(
            message.bot,
            telegram_user_id=message.from_user.id,
            text=detail,
        )
        suffix = notice_dm_sent() if sent else notice_dm_blocked()
        await message.answer(f"{compact}\n\n{suffix}")
        return

    sent = await safe_send_dm(
        message.bot,
        telegram_user_id=message.from_user.id,
        text=(
            "<b>Профайл (дэлгэрэнгүй)</b>\n"
            f"{detail}\n"
            f"<i>Олз: {message.from_user.mention_html()}</i>"
        ),
    )
    suffix = notice_dm_sent() if sent else notice_dm_blocked()
    await message.answer(f"{compact}\n\n{suffix}")
