from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from database.queries import analytics_snapshot, top_invite_users, top_reputation_users


async def build_stats(session: AsyncSession) -> dict:
    base = await analytics_snapshot(session)
    base["top_invite"] = list(await top_invite_users(session, 3))
    base["top_reputation"] = list(await top_reputation_users(session, 3))
    return base
