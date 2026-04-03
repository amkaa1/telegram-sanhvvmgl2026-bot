from sqlalchemy.ext.asyncio import AsyncSession

from database.queries import (
    get_group_stats,
    get_spam_reports,
    get_top_users_by_invites,
    get_top_users_by_reputation,
)


async def build_stats_text(session: AsyncSession) -> str:
    stats = await get_group_stats(session)
    spam_reports = await get_spam_reports(session)
    top_rep = await get_top_users_by_reputation(session, limit=3)
    top_inv = await get_top_users_by_invites(session, limit=3)

    lines: list[str] = []
    lines.append("📊 <b>Группийн статистик</b>")
    lines.append("")
    lines.append(f"👥 Нийт гишүүн (бүртгэлтэй): <b>{stats['users']}</b>")
    lines.append(f"✔ Verified гишүүн: <b>{stats.get('verified', 0)}</b>")
    lines.append(f"📨 Нийт урилга (тоологдсон): <b>{stats['invites']}</b>")
    lines.append(f"🚨 Нийт гомдол (spam/scam/fake): <b>{spam_reports}</b>")
    lines.append(f"⚠ Сэжигтэй гишүүн: <b>{stats.get('suspicious', 0)}</b>")
    lines.append(f"🎁 Шагналын босго хүрсэн: <b>{stats.get('reward_users', 0)}</b>")
    lines.append("")

    if top_rep:
        lines.append("🏆 <b>Итгэлцлийн топ гишүүд</b>")
        for i, u in enumerate(top_rep, start=1):
            lines.append(
                f"{i}. <a href=\"tg://user?id={u.telegram_id}\">{u.username or u.telegram_id}</a> "
                f"- ⭐ {u.reputation_positive} / 👎 {u.reputation_negative}"
            )
        lines.append("")

    if top_inv:
        lines.append("📨 <b>Урилгын топ гишүүд</b>")
        for i, u in enumerate(top_inv, start=1):
            lines.append(
                f"{i}. <a href=\"tg://user?id={u.telegram_id}\">{u.username or u.telegram_id}</a> "
                f"- {u.invites_count} урилга"
            )

    return "\n".join(lines)

