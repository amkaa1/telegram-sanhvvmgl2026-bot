from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from database.queries import add_report


async def submit_report(
    session: AsyncSession, reporter, reported, reason: str
):
    return await add_report(session, reporter, reported, reason)
