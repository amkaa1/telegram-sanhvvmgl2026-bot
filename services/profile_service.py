from __future__ import annotations

from html import escape

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from database.queries import get_approved_report_count
from services.reputation import resolve_badge


def _display_name(user: User) -> str:
    full = " ".join(filter(None, [user.first_name, user.last_name])).strip()
    if full:
        return full
    if user.username:
        return f"@{user.username}"
    return str(user.telegram_id)


def _username_text(user: User) -> str:
    return f"@{user.username}" if user.username else "-"


def _trust_value(user: User) -> int:
    return max(0, user.reputation_positive - user.reputation_negative)


async def format_profile_text(session: AsyncSession, user: User) -> str:
    approved_reports = await get_approved_report_count(session, user.id)
    badge = resolve_badge(user)
    trust_level = _trust_value(user)
    return "\n".join(
        [
            "━━━━━━━━━━━━━━━",
            f"👤 Профайл: {escape(_display_name(user))}",
            f"🔗 Username: {escape(_username_text(user))}",
            "━━━━━━━━━━━━━━━",
            f"🏷 Badge: {escape(badge)}",
            f"✅ Trust Level: {trust_level}",
            f"👍 Good: {user.reputation_positive}",
            f"👎 Bad: {user.reputation_negative}",
            f"⚠️ Reports: {approved_reports}",
            f"📨 Invites: {user.invites_count}",
            "━━━━━━━━━━━━━━━",
        ]
    )
