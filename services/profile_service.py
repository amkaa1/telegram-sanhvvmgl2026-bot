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


def _trust_level_label(points: int, badge: str) -> str:
    if badge == "Verified":
        return "Verified"
    if points < 10:
        return "Шинэ гишүүн"
    if points < 50:
        return "Идэвхтэй гишүүн"
    if points < 200:
        return "Итгэлтэй гишүүн"
    return "Verified"


async def format_profile_text(session: AsyncSession, user: User) -> str:
    approved_reports = await get_approved_report_count(session, user.id)
    badge = resolve_badge(user)
    trust_points = _trust_value(user)
    trust_level = _trust_level_label(trust_points, badge)
    return "\n".join(
        [
            "━━━━━━━━━━━━━━━",
            f"💀 Профайл: {escape(_display_name(user))}",
            f"🔗 Username: {escape(_username_text(user))}",
            "━━━━━━━━━━━━━━━",
            f"✅ Trust Level: {escape(trust_level)}",
            f"👍 Good: {user.reputation_positive}",
            f"👎 Bad: {user.reputation_negative}",
            f"📨 Invite: {user.invites_count}",
            f"⚠️ Reports: {approved_reports}",
            "━━━━━━━━━━━━━━━",
            "SanhvvMGL2026",
        ]
    )
