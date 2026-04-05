"""Formatted reward milestone messages (Mongolian, HTML)."""

from html import escape

from database.models import User


def format_reward_group_announcement(inviter: User, count: int, amount_mnt: int) -> str:
    """Public group announcement when inviter reaches a reward threshold."""
    reward_fmt = f"{amount_mnt:,}"
    uname = inviter.username
    if uname:
        who = f"@{escape(uname)}"
    else:
        name = (inviter.first_name or "").strip() or str(inviter.telegram_id)
        who = f'<a href="tg://user?id={inviter.telegram_id}">{escape(name)}</a>'
    return (
        f"🏆 Баяр хүргэе, {who}!\n\n"
        f"Таны invite count {count} хүрч,\n"
        f"{reward_fmt}₮💵 авах эрхтэй боллоо 🔥\n\n"
        "📩 Админ руу чат бичиж шагналаа аваарай."
    )
