"""Private DM helpers and short group notices (aiogram 3.x)."""

from __future__ import annotations

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup

from config import settings
from utils.logger import logger


async def safe_send_dm(
    bot: Bot,
    *,
    telegram_user_id: int,
    text: str,
    parse_mode: str | None = "HTML",
    disable_notification: bool | None = None,
    reply_markup: InlineKeyboardMarkup | ReplyKeyboardMarkup | None = None,
) -> bool:
    """
    Send a private message to a user. Returns True if Telegram accepted the send.
    Handles blocked / not-started / deleted chat without raising.
    """
    try:
        await bot.send_message(
            telegram_user_id,
            text,
            parse_mode=parse_mode,
            disable_notification=disable_notification,
            reply_markup=reply_markup,
        )
        return True
    except TelegramForbiddenError:
        logger.info("safe_send_dm: forbidden user_id=%s", telegram_user_id)
        return False
    except TelegramBadRequest as exc:
        logger.info(
            "safe_send_dm: bad_request user_id=%s err=%s",
            telegram_user_id,
            exc,
        )
        return False
    except Exception:
        logger.exception("safe_send_dm: unexpected user_id=%s", telegram_user_id)
        return False


def notice_dm_sent() -> str:
    return "Дэлгэрэнгүй мэдээллийг хувийн чат руу илгээлээ."


def notice_dm_blocked() -> str:
    return (
        "Хувийн чат руу илгээж чадсангүй. Эхлээд bot-оо нээгээд "
        f"<code>/start</code> дарна уу: @{settings.bot_username}"
    )


def notice_callback_expired() -> str:
    return "Энэ үйлдэл түр хүчингүй болсон байна."
