from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from database.queries import create_report


async def submit_report(session: AsyncSession, reporter, reported, reason: str):
    return await create_report(session, reporter, reported, reason)
