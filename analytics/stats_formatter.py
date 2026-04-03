from __future__ import annotations


def format_stats(data: dict) -> str:
    return (
        "📊 Статистик\n"
        f"Нийт хэрэглэгч: {data['total_users']}\n"
        f"Verified: {data['total_verified']}\n"
        f"Нийт invite: {data['total_invites']}\n"
        f"Нийт report: {data['total_reports']}\n"
        f"Сэжигтэй: {data['suspicious_users']}\n"
        f"Шагналын босго хүрсэн: {data['reward_reached_users']}"
    )
