from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from database.queries import get_or_create_user


async def sync_user(session: AsyncSession, tg_user):
    return await get_or_create_user(
        session=session,
        telegram_id=tg_user.id,
        username=tg_user.username,
        first_name=tg_user.first_name,
        last_name=tg_user.last_name,
    )
