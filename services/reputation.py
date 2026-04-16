from dataclasses import dataclass

from aiogram.types import User as TgUser
from sqlalchemy.ext.asyncio import AsyncSession

from database.queries import add_rating, can_rate_user, get_or_create_user
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


async def ensure_user(
    session: AsyncSession,
    tg_user: TgUser,
) -> User:
    return await get_or_create_user(
        session=session,
        telegram_id=tg_user.id,
        username=tg_user.username,
        first_name=tg_user.first_name,
        last_name=tg_user.last_name,
    )


@dataclass(frozen=True)
class RatingResult:
    ok: bool
    group_line: str
    detail_html: str | None


async def rate_user(
    session: AsyncSession,
    from_tg: TgUser,
    to_tg: TgUser,
    positive: bool,
) -> RatingResult:
    from_user = await ensure_user(session, from_tg)
    to_user = await ensure_user(session, to_tg)

    if from_user.id == to_user.id:
        return RatingResult(
            ok=False,
            group_line="Өөрийгөө үнэлэх боломжгүй.",
            detail_html=None,
        )

    allowed = await can_rate_user(session, from_user, to_user)
    if not allowed:
        return RatingResult(
            ok=False,
            group_line=(
                "72 цагийн хугацаанд хамгийн ихдээ 2 өөр гишүүнд үнэлгээ өгөх боломжтой. "
                "Дараа дахин оролдоно уу."
            ),
            detail_html=None,
        )

    await add_rating(session, from_user, to_user, positive)
    to_user.verified = is_verified(to_user.reputation_positive)
    await session.commit()

    level = get_trust_level(to_user.reputation_positive)
    action = "Дэмжлэг" if positive else "Сэрэмжлүүлэг"
    group_line = (
        f"{'👍' if positive else '👎'} {to_tg.mention_html()} — <b>{action}</b> бүртгэгдлээ. "
        f"Trust: <b>{level}</b>"
    )
    if positive:
        detail = (
            f"{to_tg.mention_html()} — <b>сайн үнэлгээ</b> авлаа.\n"
            f"Trust түвшин: <b>{level}</b>"
        )
    else:
        detail = (
            f"{to_tg.mention_html()} — <b>сэрэмжлүүлэг</b> бүртгэгдлээ.\n"
            f"Trust түвшин: <b>{level}</b>"
        )
    return RatingResult(ok=True, group_line=group_line, detail_html=detail)

