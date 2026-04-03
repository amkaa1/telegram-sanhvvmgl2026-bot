import json
import time
from html import escape
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession  # type: ignore[import-unresolved]

from database.queries import (
    get_group_stats,
    get_spam_reports,
    get_top_users_by_invites,
    get_top_users_by_reputation,
)

LOG_PATH = Path(__file__).resolve().parents[1] / "debug-20ebd7.log"


async def build_stats_text(session: AsyncSession) -> str:
    # #region agent log
    payload = {
        "sessionId": "20ebd7",
        "runId": "pre-fix",
        "hypothesisId": "H6_stats_crash_or_formatting",
        "location": "analytics/stats.py:build_stats_text",
        "message": "build_stats_text start",
        "data": {},
        "timestamp": int(time.time() * 1000),
    }
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001
        print("DEBUGLOG_WRITE_FAIL: analytics/stats.py:build_stats_text:start")
    # #endregion

    try:
        stats = await get_group_stats(session)
        spam_reports = await get_spam_reports(session)
        top_rep = await get_top_users_by_reputation(session, limit=3)
        top_inv = await get_top_users_by_invites(session, limit=3)
    except Exception as exc:  # noqa: BLE001
        # #region agent log
        payload = {
            "sessionId": "20ebd7",
            "runId": "pre-fix",
            "hypothesisId": "H6_stats_crash_or_formatting",
            "location": "analytics/stats.py:build_stats_text",
            "message": "build_stats_text exception",
            "data": {"error_type": type(exc).__name__},
            "timestamp": int(time.time() * 1000),
        }
        try:
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=False) + "\n")
        except Exception:  # noqa: BLE001
            print("DEBUGLOG_WRITE_FAIL: analytics/stats.py:build_stats_text:exception")
        # #endregion
        print("DEBUG_BUILD_STATS_EXCEPTION", f"error={type(exc).__name__}", f"msg={exc}")
        raise

    lines: list[str] = []
    lines.append("📊 <b>Группийн статистик</b>")
    lines.append("")
    lines.append(f"👥 Нийт гишүүн (бүртгэлтэй): <b>{stats['users']:,}</b>")
    lines.append(f"✔ Баталгаажсан гишүүн: <b>{stats.get('verified', 0):,}</b>")
    lines.append(f"📨 Нийт урилга (тоологдсон): <b>{stats['invites']:,}</b>")
    lines.append(f"🚨 Нийт гомдол (spam/scam/fake): <b>{spam_reports:,}</b>")
    lines.append(f"⚠ Сэжигтэй гишүүн: <b>{stats.get('suspicious', 0):,}</b>")
    lines.append(f"🎁 Шагналын босго хүрсэн: <b>{stats.get('reward_users', 0):,}</b>")
    lines.append("")

    if top_rep:
        lines.append("🏆 <b>Итгэлцлийн топ гишүүд</b>")
        for i, u in enumerate(top_rep, start=1):
            label = escape(u.username) if u.username else str(u.telegram_id)
            lines.append(
                f"{i}. <a href=\"tg://user?id={u.telegram_id}\">{label}</a> "
                f"- ⭐ {u.reputation_positive} / 👎 {u.reputation_negative}"
            )
        lines.append("")

    if top_inv:
        lines.append("📨 <b>Хамгийн их invite хийсэн гишүүд</b>")
        for i, u in enumerate(top_inv, start=1):
            label = escape(u.username) if u.username else str(u.telegram_id)
            lines.append(
                f"{i}. <a href=\"tg://user?id={u.telegram_id}\">{label}</a> "
                f"- {u.invites_count:,} урилга"
            )

    result = "\n".join(lines)
    print("DEBUG_BUILD_STATS_RESULT", f"len={len(result)}")
    return result

