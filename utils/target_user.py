"""Resolve target Telegram user from reply, mention, @username, or numeric id."""

from __future__ import annotations

from aiogram.enums import ChatType
from aiogram.types import Message, User as TgUser

from database.db import SessionLocal
from database.queries import get_or_create_user, get_user_by_username

UNKNOWN_USER_TEXT = "⚠️ Энэ хэрэглэгчийг одоогоор таньж чадсангүй ⚠️"


def _strip_command_args(text: str) -> str:
    t = (text or "").strip()
    if not t:
        return ""
    parts = t.split(maxsplit=1)
    if len(parts) == 1:
        return ""
    return parts[1].strip()


async def _fetch_private_user(bot, telegram_id: int) -> TgUser | None:
    try:
        chat = await bot.get_chat(telegram_id)
    except Exception:
        return None
    if chat.type != ChatType.PRIVATE:
        return None
    return TgUser(
        id=int(chat.id),
        is_bot=bool(getattr(chat, "is_bot", False)),
        first_name=getattr(chat, "first_name", "") or "",
        last_name=getattr(chat, "last_name", None),
        username=getattr(chat, "username", None),
    )


async def _resolve_username_arg(message: Message, username: str) -> tuple[TgUser | None, str | None]:
    if not username:
        return None, UNKNOWN_USER_TEXT
    async with SessionLocal() as session:
        user = await get_user_by_username(session, username)
        if user is not None:
            return (
                TgUser(
                    id=user.telegram_id,
                    is_bot=user.is_bot,
                    first_name=user.first_name or "",
                    last_name=user.last_name,
                    username=user.username,
                ),
                None,
            )
    try:
        chat = await message.bot.get_chat(f"@{username}")
    except Exception:
        return None, UNKNOWN_USER_TEXT
    if chat.type != ChatType.PRIVATE:
        return None, UNKNOWN_USER_TEXT
    if getattr(chat, "is_bot", False):
        return None, "Bot-д энэ үйлдэл хийх боломжгүй."
    async with SessionLocal() as session:
        await get_or_create_user(
            session,
            telegram_id=int(chat.id),
            username=getattr(chat, "username", None),
            first_name=getattr(chat, "first_name", None),
            last_name=getattr(chat, "last_name", None),
        )
        await session.commit()
    return (
        TgUser(
            id=int(chat.id),
            is_bot=False,
            first_name=getattr(chat, "first_name", "") or "",
            last_name=getattr(chat, "last_name", None),
            username=getattr(chat, "username", None),
        ),
        None,
    )


async def resolve_profile_target(
    message: Message,
    *,
    command_names: tuple[str, ...] = ("/profile",),
) -> tuple[TgUser | None, str | None]:
    """
    Profile: default target is sender. Returns error only when username/id invalid.
    """
    if message.from_user is None:
        return None, UNKNOWN_USER_TEXT

    if message.reply_to_message and message.reply_to_message.from_user:
        t = message.reply_to_message.from_user
        if t.is_bot:
            return None, "Bot-ын профайл харах боломжгүй."
        return t, None

    text = (message.text or "").strip()
    lower = text.lower()
    for cmd in command_names:
        if lower.startswith(cmd + "@"):
            token = text.split("@", 1)[1].split(maxsplit=1)[0].strip()
            if not token:
                return None, UNKNOWN_USER_TEXT
            return await _resolve_username_arg(message, token.lstrip("@"))

    if message.entities:
        for ent in message.entities:
            if ent.type == "mention":
                raw = text[ent.offset : ent.offset + ent.length]
                uname = raw.lstrip("@")
                return await _resolve_username_arg(message, uname)
            if ent.type == "text_mention" and ent.user:
                if ent.user.is_bot:
                    return None, "Bot-ын профайл харах боломжгүй."
                return ent.user, None

    rest = _strip_command_args(text)
    if not rest:
        return message.from_user, None

    first = rest.split(maxsplit=1)[0].strip()
    if first.startswith("@"):
        return await _resolve_username_arg(message, first[1:].strip())

    if first.isdigit() and len(first) >= 5:
        u = await _fetch_private_user(message.bot, int(first))
        if u is None:
            return None, UNKNOWN_USER_TEXT
        return u, None

    return message.from_user, None


async def resolve_rating_target(
    message: Message,
    *,
    command_names: tuple[str, ...] = ("/good", "/bad"),
) -> tuple[TgUser | None, str | None]:
    """
    Rating requires explicit target: reply, mention, @user, or numeric id.
    """
    if message.from_user is None:
        return None, UNKNOWN_USER_TEXT

    if message.reply_to_message and message.reply_to_message.from_user:
        t = message.reply_to_message.from_user
        if t.is_bot:
            return None, "Bot-д энэ үйлдэл хийх боломжгүй."
        return t, None

    text = (message.text or "").strip()
    lower = text.lower()
    for cmd in command_names:
        if lower.startswith(cmd + "@"):
            token = text.split("@", 1)[1].split(maxsplit=1)[0].strip()
            if not token:
                return None, UNKNOWN_USER_TEXT
            return await _resolve_username_arg(message, token.lstrip("@"))

    if message.entities:
        for ent in message.entities:
            if ent.type == "mention":
                raw = text[ent.offset : ent.offset + ent.length]
                uname = raw.lstrip("@")
                return await _resolve_username_arg(message, uname)
            if ent.type == "text_mention" and ent.user:
                if ent.user.is_bot:
                    return None, "Bot-д энэ үйлдэл хийх боломжгүй."
                return ent.user, None

    rest = _strip_command_args(text)
    if not rest:
        return None, None

    first = rest.split(maxsplit=1)[0].strip()
    if first.startswith("@"):
        return await _resolve_username_arg(message, first[1:].strip())

    if first.isdigit() and len(first) >= 5:
        u = await _fetch_private_user(message.bot, int(first))
        if u is None:
            return None, UNKNOWN_USER_TEXT
        return u, None

    return None, UNKNOWN_USER_TEXT
