from __future__ import annotations

from aiogram.types import User as TgUser
from sqlalchemy.ext.asyncio import AsyncSession

from database.queries import get_or_create_user


async def ensure_user_registered(session: AsyncSession, tg_user: TgUser):
    user = await get_or_create_user(
        session,
        telegram_id=tg_user.id,
        username=tg_user.username,
        first_name=tg_user.first_name,
        last_name=tg_user.last_name,
    )
    user.is_bot = tg_user.is_bot
    await session.flush()
    return user


async def has_private_started(session: AsyncSession, tg_user: TgUser) -> bool:
    user = await ensure_user_registered(session, tg_user)
    return bool(user.bot_private_started)
