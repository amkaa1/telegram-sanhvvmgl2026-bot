from __future__ import annotations

import hashlib

from aiogram import Bot
from aiogram.types import User as TgUser
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database.models import User
from database.queries import (
    get_or_create_user,
    get_top_users_by_invites,
    increment_invite,
)
from utils.logger import logger


INVITE_REWARDS = [
    (500, 75000),
    (1000, 150000),
    (2000, 300000),
    (5000, 700000),
]


def build_invite_payload(user_id: int) -> str:
    # payload is шууд хэрэглэгчийн ID-г ашиглана (hash биш) –
    # ингэснээр /start payload-аас урилга өгсөн хүнийг шууд тодорхойлно.
    return str(user_id)


async def get_personal_invite_link(bot: Bot, user_id: int) -> str:
    # Telegram deep-link: https://t.me/<bot>?start=<payload>
    me = await bot.me()
    payload = build_invite_payload(user_id)
    return f"https://t.me/{me.username}?start={payload}"


async def handle_new_member(
    session: AsyncSession,
    inviter_tg: TgUser | None,
    new_tg: TgUser,
    link_hash: str | None,
    bot: Bot,
) -> None:
    invited_user = await get_or_create_user(
        session,
        telegram_id=new_tg.id,
        username=new_tg.username,
        first_name=new_tg.first_name,
        last_name=new_tg.last_name,
    )

    if not inviter_tg or not link_hash:
        return

    inviter = await get_or_create_user(
        session,
        telegram_id=inviter_tg.id,
        username=inviter_tg.username,
        first_name=inviter_tg.first_name,
        last_name=inviter_tg.last_name,
    )

    invite = await increment_invite(session, inviter, invited_user, link_hash)
    if not invite:
        await session.commit()
        return

    await session.commit()

    await _check_and_notify_rewards(bot, inviter)


async def _check_and_notify_rewards(bot: Bot, inviter: User) -> None:
    for threshold, amount in INVITE_REWARDS:
        if inviter.invites_count == threshold:
            text = (
                "🎉 <b>Урилгын шагналын босго давлаа!</b>\n\n"
                f"👤 Гишүүн: <a href=\"tg://user?id={inviter.telegram_id}\">{inviter.username or inviter.telegram_id}</a>\n"
                f"📨 Урилга: <b>{inviter.invites_count}</b>\n"
                f"💰 Шагнал: <b>{amount:,}₮</b>"
            )
            for admin_id in settings.admin_ids:
                try:
                    await bot.send_message(admin_id, text)
                except Exception as exc:  # noqa: BLE001
                    logger.error("Failed to notify admin %s: %s", admin_id, exc)


async def get_invite_leaderboard(session: AsyncSession, limit: int = 10):
    return await get_top_users_by_invites(session, limit=limit)

