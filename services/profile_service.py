from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from database.queries import get_user_by_telegram_id, get_user_by_username


async def resolve_profile_target(session: AsyncSession, arg: str | None, reply_user_id: int | None, self_user_id: int):
    if reply_user_id:
        return await get_user_by_telegram_id(session, reply_user_id)
    if arg and arg.startswith("@"):
        user = await get_user_by_username(session, arg)
        if user:
            return user
    if arg and arg.isdigit():
        return await get_user_by_telegram_id(session, int(arg))
    return await get_user_by_telegram_id(session, self_user_id)
