from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from database.queries import top_bad_users, top_good_users, top_invite_users, top_reputation_users


async def get_leaderboards(session: AsyncSession) -> dict[str, list]:
    return {
        "invite": list(await top_invite_users(session)),
        "good": list(await top_good_users(session)),
        "bad": list(await top_bad_users(session)),
        "reputation": list(await top_reputation_users(session)),
    }
