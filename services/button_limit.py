"""Per-user cooldown and burst lock for inline callbacks in group/supergroup chats."""

from __future__ import annotations

import datetime as dt
from enum import Enum, auto

from aiogram.enums import ChatType
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import GroupButtonThrottle
from utils.logger import logger

COOLDOWN_SECONDS = 20
BURST_WINDOW_SECONDS = 600
BURST_MAX_PRESSES = 5
LOCK_SECONDS = 600

MSG_COOLDOWN = (
    "⏳ Түр хүлээнэ үү. Дахин дарахаас өмнө хэдэн секунд хүлээнэ үү."
)
MSG_BURST_LOCK = (
    "🔒 Та хэт олон удаа дарлаа. 10 минутын дараа дахин оролдоно уу."
)


class GroupButtonGuardResult(Enum):
    OK = auto()
    COOLDOWN = auto()
    LOCKED = auto()
    NEWLY_LOCKED = auto()


def is_group_chat(message: Message | None) -> bool:
    if message is None or message.chat is None:
        return False
    return message.chat.type in {ChatType.GROUP, ChatType.SUPERGROUP}


async def _get_or_create_throttle(
    session: AsyncSession, telegram_user_id: int
) -> GroupButtonThrottle:
    stmt = select(GroupButtonThrottle).where(
        GroupButtonThrottle.telegram_user_id == telegram_user_id
    )
    res = await session.execute(stmt)
    row = res.scalar_one_or_none()
    if row is not None:
        return row
    row = GroupButtonThrottle(telegram_user_id=telegram_user_id, burst_count=0)
    session.add(row)
    await session.flush()
    return row


async def check_and_record_group_button_press(
    session: AsyncSession,
    *,
    telegram_user_id: int,
    is_admin: bool,
) -> GroupButtonGuardResult:
    """
    Enforce burst window + lock, then per-user cooldown (skipped for admins).
    Call only for group/supergroup callbacks.
    """
    now = dt.datetime.now(dt.timezone.utc)

    row = await _get_or_create_throttle(session, telegram_user_id)

    if row.locked_until is not None and row.locked_until > now:
        logger.info(
            "group_button_guard: burst_lock active user_id=%s until=%s",
            telegram_user_id,
            row.locked_until.isoformat(),
        )
        return GroupButtonGuardResult.LOCKED

    if (
        row.burst_window_start is None
        or (now - row.burst_window_start).total_seconds() > BURST_WINDOW_SECONDS
    ):
        row.burst_window_start = now
        row.burst_count = 0

    row.burst_count += 1
    row.updated_at = now

    if row.burst_count > BURST_MAX_PRESSES:
        row.locked_until = now + dt.timedelta(seconds=LOCK_SECONDS)
        await session.flush()
        logger.warning(
            "group_button_guard: burst_lock SET user_id=%s presses_in_window=%s",
            telegram_user_id,
            row.burst_count,
        )
        return GroupButtonGuardResult.NEWLY_LOCKED

    if not is_admin:
        if row.last_press_at is not None:
            delta = (now - row.last_press_at).total_seconds()
            if delta < COOLDOWN_SECONDS:
                await session.flush()
                logger.info(
                    "group_button_guard: cooldown user_id=%s delta_s=%.2f",
                    telegram_user_id,
                    delta,
                )
                return GroupButtonGuardResult.COOLDOWN
        row.last_press_at = now

    await session.flush()
    return GroupButtonGuardResult.OK


async def answer_guard_failure(
    call: CallbackQuery, result: GroupButtonGuardResult
) -> None:
    if result == GroupButtonGuardResult.COOLDOWN:
        await call.answer(MSG_COOLDOWN, show_alert=True)
    elif result in (GroupButtonGuardResult.LOCKED, GroupButtonGuardResult.NEWLY_LOCKED):
        await call.answer(MSG_BURST_LOCK, show_alert=True)
