from dataclasses import dataclass
from html import escape

from aiogram.types import Message
from aiogram.types import User as TgUser
from sqlalchemy.ext.asyncio import AsyncSession

from database.queries import (
    RATING_DAILY_LIMIT,
    add_rating,
    count_recent_ratings,
    create_rating_undo_token,
    get_or_create_user,
    get_rating_cooldown_remaining,
)
from database.models import User


TRUST_LEVELS = [
    (0, 10, "Шинэ гишүүн"),
    (10, 50, "Идэвхтэй гишүүн"),
    (50, 200, "Итгэлтэй гишүүн"),
    (200, 10 ** 9, "Verified"),
]


def get_trust_level(positive: int) -> str:
    for low, high, label in TRUST_LEVELS:
        if low <= positive < high:
            return label
    return "Шинэ гишүүн"


def is_verified(positive: int) -> bool:
    return positive >= 200


def format_remaining_time(seconds: int) -> str:
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    parts: list[str] = []
    if hours:
        parts.append(f"{hours}ц")
    if minutes:
        parts.append(f"{minutes}м")
    if secs or not parts:
        parts.append(f"{secs}с")
    return " ".join(parts)


def get_user_display_label(tg_user: TgUser) -> str:
    if tg_user.username:
        return f"@{escape(tg_user.username)}"
    full_name = " ".join(filter(None, [tg_user.first_name, tg_user.last_name])).strip()
    if full_name:
        return escape(full_name)
    return str(tg_user.id)


def resolve_badge(user: User) -> str:
    if user.manual_badge_override:
        return user.manual_badge_override
    return get_trust_level(user.reputation_positive)


async def ensure_user(
    session: AsyncSession,
    tg_user: TgUser,
) -> User:
    user = await get_or_create_user(
        session=session,
        telegram_id=tg_user.id,
        username=tg_user.username,
        first_name=tg_user.first_name,
        last_name=tg_user.last_name,
    )
    user.is_bot = tg_user.is_bot
    await session.flush()
    return user


@dataclass(frozen=True)
class RatingResult:
    ok: bool
    group_line: str
    dm_line: str | None
    undo_token: str | None = None


async def rate_user(
    session: AsyncSession,
    from_tg: TgUser,
    to_tg: TgUser,
    positive: bool,
    *,
    source_message: Message | None = None,
) -> RatingResult:
    from_user = await ensure_user(session, from_tg)
    to_user = await ensure_user(session, to_tg)
    label = get_user_display_label(to_tg)
    rate_word = "good" if positive else "bad"

    if from_user.id == to_user.id:
        return RatingResult(
            ok=False,
            group_line="⚠️ Өөрийгөө үнэлэх боломжгүй ⚠️",
            dm_line=None,
        )

    recent_count = await count_recent_ratings(session, actor_user_id=from_user.id, hours=24)
    if recent_count >= RATING_DAILY_LIMIT:
        remaining = await get_rating_cooldown_remaining(session, actor_user_id=from_user.id)
        remaining_text = format_remaining_time(
            int(remaining.total_seconds()) if remaining else 0
        )
        return RatingResult(
            ok=False,
            group_line=(
                "⏳ Та өнөөдрийн rating limit-дээ хүрсэн байна ⏳\n"
                f"Дахин үнэлгээ өгөх боломж: {remaining_text}"
            ),
            dm_line=None,
        )

    source_chat_type = source_message.chat.type if source_message and source_message.chat else None
    source_chat_id = source_message.chat.id if source_message and source_message.chat else None
    source_message_id = source_message.message_id if source_message else None
    rating = await add_rating(
        session,
        from_user,
        to_user,
        positive,
        source_chat_type=source_chat_type,
        source_chat_id=source_chat_id,
        source_message_id=source_message_id,
    )
    if rating is None:
        return RatingResult(ok=False, group_line="Системийн алдаа гарлаа.", dm_line=None)
    to_user.verified = is_verified(to_user.reputation_positive)
    undo = await create_rating_undo_token(
        session,
        rating_id=rating.id,
        actor_telegram_id=from_tg.id,
    )
    await session.commit()

    group_line = f"✅ {label}-д {rate_word} үнэлгээг бүртгэлээ ✅"
    dm_line = f"✅ Та {label}-д {rate_word} үнэлгээ өглөө ✅"
    return RatingResult(ok=True, group_line=group_line, dm_line=dm_line, undo_token=undo.token)

