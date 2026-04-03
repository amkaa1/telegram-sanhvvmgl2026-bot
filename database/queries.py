import datetime as dt
import json
import time
from pathlib import Path
from typing import Iterable, Sequence

from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Invite, MessageLog, Mute, Rating, Report, User, Warning


RATING_WINDOW_HOURS = 72
RATING_MAX_TARGETS_PER_WINDOW = 2

LOG_PATH = Path(__file__).resolve().parents[1] / "debug-20ebd7.log"


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None,
    first_name: str | None,
    last_name: str | None,
) -> User:
    stmt = select(User).where(User.telegram_id == telegram_id)
    res = await session.execute(stmt)
    user = res.scalar_one_or_none()
    if user:
        updated = False
        if username is not None and user.username != username:
            user.username = username
            updated = True
        if first_name is not None and user.first_name != first_name:
            user.first_name = first_name
            updated = True
        if last_name is not None and user.last_name != last_name:
            user.last_name = last_name
            updated = True
        if updated:
            await session.flush()
        return user
    user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
    )
    session.add(user)
    await session.flush()
    return user


def _rating_window_key(now: dt.datetime) -> str:
    # bucket by 72h periods from epoch
    epoch = dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=dt.timezone.utc)
    delta = now - epoch
    bucket = int(delta.total_seconds() // (RATING_WINDOW_HOURS * 3600))
    return f"w{bucket}"


async def can_rate_user(
    session: AsyncSession, from_user: User, to_user: User
) -> bool:
    if from_user.id == to_user.id:
        return False
    now = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc)
    window_key = _rating_window_key(now)

    # count distinct targets in window
    stmt = (
        select(func.count(func.distinct(Rating.to_user_id)))
        .where(
            and_(
                Rating.from_user_id == from_user.id,
                Rating.created_window == window_key,
            )
        )
    )
    res = await session.execute(stmt)
    count_targets = res.scalar_one() or 0
    if count_targets >= RATING_MAX_TARGETS_PER_WINDOW:
        # already rated 2 different users
        # However might still allow rating same user again only once – but spec says
        # "2 different users", so we forbid new unique targets.
        stmt_same = select(Rating).where(
            and_(
                Rating.from_user_id == from_user.id,
                Rating.to_user_id == to_user.id,
                Rating.created_window == window_key,
            )
        )
        res_same = await session.execute(stmt_same)
        existing_same = res_same.scalar_one_or_none()
        return existing_same is not None
    return True


async def add_rating(
    session: AsyncSession, from_user: User, to_user: User, is_positive: bool
) -> Rating | None:
    if from_user.id == to_user.id:
        return None

    now = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc)
    window_key = _rating_window_key(now)

    stmt = select(Rating).where(
        and_(
            Rating.from_user_id == from_user.id,
            Rating.to_user_id == to_user.id,
            Rating.created_window == window_key,
        )
    )
    res = await session.execute(stmt)
    rating = res.scalar_one_or_none()
    if rating:
        # update existing rating in this window
        if rating.is_positive != is_positive:
            if is_positive:
                to_user.reputation_positive += 1
                to_user.reputation_negative -= 1
            else:
                to_user.reputation_positive -= 1
                to_user.reputation_negative += 1
            rating.is_positive = is_positive
            await session.flush()
        return rating

    # new rating
    rating = Rating(
        from_user_id=from_user.id,
        to_user_id=to_user.id,
        is_positive=is_positive,
        created_window=window_key,
    )
    session.add(rating)
    if is_positive:
        to_user.reputation_positive += 1
    else:
        to_user.reputation_negative += 1
    await session.flush()
    return rating


async def increment_invite(
    session: AsyncSession,
    inviter: User,
    invited: User,
    link_hash: str,
) -> Invite | None:
    stmt = select(Invite).where(
        and_(
            Invite.inviter_id == inviter.id,
            Invite.invited_user_id == invited.id,
        )
    )
    res = await session.execute(stmt)
    duplicate_exists = res.scalar_one_or_none() is not None
    if duplicate_exists:
        # #region agent log
        payload = {
            "sessionId": "20ebd7",
            "runId": "pre-fix",
            "hypothesisId": "H8_referral_double_counting_or_non_join_events",
            "location": "database/queries.py:increment_invite",
            "message": "Invite insert skipped (duplicate exists)",
            "data": {"link_hash": link_hash},
            "timestamp": int(time.time() * 1000),
        }
        try:
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=False) + "\n")
        except Exception:  # noqa: BLE001
            print("DEBUGLOG_WRITE_FAIL: database/queries.py:increment_invite:dup")
        # #endregion
        return None
    invite = Invite(
        inviter_id=inviter.id, invited_user_id=invited.id, link_hash=link_hash
    )
    session.add(invite)
    try:
        async with session.begin_nested():
            await session.flush()
    except IntegrityError:
        session.expunge(invite)
        # #region agent log
        try:
            payload = {
                "sessionId": "20ebd7",
                "runId": "pre-fix",
                "hypothesisId": "H8_referral_double_counting_or_non_join_events",
                "location": "database/queries.py:increment_invite",
                "message": "Invite insert skipped (integrity race)",
                "data": {"link_hash": link_hash},
                "timestamp": int(time.time() * 1000),
            }
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=False) + "\n")
        except Exception:  # noqa: BLE001
            pass
        # #endregion
        return None
    inviter.invites_count += 1
    await session.flush()
    # #region agent log
    payload = {
        "sessionId": "20ebd7",
        "runId": "pre-fix",
        "hypothesisId": "H8_referral_double_counting_or_non_join_events",
        "location": "database/queries.py:increment_invite",
        "message": "Invite inserted",
        "data": {"link_hash": link_hash},
        "timestamp": int(time.time() * 1000),
    }
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001
        print("DEBUGLOG_WRITE_FAIL: database/queries.py:increment_invite:inserted")
    # #endregion
    return invite


async def add_report(
    session: AsyncSession,
    reporter: User,
    reported: User,
    reason: str,
) -> Report:
    report = Report(
        reporter_id=reporter.id,
        reported_user_id=reported.id,
        reason=reason,
    )
    session.add(report)
    await session.flush()
    return report


async def add_warning(
    session: AsyncSession, user: User, reason: str | None
) -> Warning:
    warning = Warning(user_id=user.id, reason=reason)
    session.add(warning)
    await session.flush()
    return warning


async def get_warning_count(session: AsyncSession, user: User) -> int:
    stmt = select(func.count(Warning.id)).where(Warning.user_id == user.id)
    res = await session.execute(stmt)
    return int(res.scalar_one() or 0)


async def set_mute(
    session: AsyncSession, user: User, until: dt.datetime | None
) -> Mute:
    stmt = select(Mute).where(Mute.user_id == user.id)
    res = await session.execute(stmt)
    mute = res.scalar_one_or_none()
    if mute:
        mute.until = until
    else:
        mute = Mute(user_id=user.id, until=until)
        session.add(mute)
    await session.flush()
    return mute


async def log_message(session: AsyncSession, user: User) -> None:
    log = MessageLog(user_id=user.id)
    session.add(log)
    await session.flush()


async def get_recent_message_count(
    session: AsyncSession, user: User, seconds: int
) -> int:
    now = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc)
    cutoff = now - dt.timedelta(seconds=seconds)
    stmt = select(func.count(MessageLog.id)).where(
        and_(MessageLog.user_id == user.id, MessageLog.created_at >= cutoff)
    )
    res = await session.execute(stmt)
    return int(res.scalar_one() or 0)


async def get_top_users_by_reputation(
    session: AsyncSession, limit: int = 10
) -> Sequence[User]:
    stmt = (
        select(User)
        .order_by(User.reputation_positive.desc(), User.reputation_negative.asc())
        .limit(limit)
    )
    res = await session.execute(stmt)
    return res.scalars().all()


async def get_top_users_by_invites(
    session: AsyncSession, limit: int = 10
) -> Sequence[User]:
    stmt = select(User).order_by(User.invites_count.desc()).limit(limit)
    res = await session.execute(stmt)
    return res.scalars().all()


async def get_group_stats(
    session: AsyncSession,
) -> dict[str, int]:
    stmt_users = select(func.count(User.id))
    users_count = int((await session.execute(stmt_users)).scalar_one() or 0)

    stmt_reports = select(func.count(Report.id))
    reports_count = int((await session.execute(stmt_reports)).scalar_one() or 0)

    stmt_invites = select(func.sum(User.invites_count))
    invites_total = int((await session.execute(stmt_invites)).scalar_one() or 0)

    stmt_verified = select(func.count(User.id)).where(User.verified.is_(True))
    verified_count = int((await session.execute(stmt_verified)).scalar_one() or 0)

    stmt_suspicious = select(func.count(User.id)).where(User.is_suspicious.is_(True))
    suspicious_count = int((await session.execute(stmt_suspicious)).scalar_one() or 0)

    stmt_rewards = select(func.count(User.id)).where(
        or_(
            User.reward_500_sent.is_(True),
            User.reward_1000_sent.is_(True),
            User.reward_2000_sent.is_(True),
            User.reward_5000_sent.is_(True),
        )
    )
    reward_users = int((await session.execute(stmt_rewards)).scalar_one() or 0)

    return {
        "users": users_count,
        "reports": reports_count,
        "invites": invites_total,
        "verified": verified_count,
        "suspicious": suspicious_count,
        "reward_users": reward_users,
    }


async def get_spam_reports(
    session: AsyncSession,
) -> int:
    stmt = select(func.count(Report.id)).where(
        Report.reason.in_(["spam", "scam", "fake"])
    )
    res = await session.execute(stmt)
    return int(res.scalar_one() or 0)


async def get_users_by_ids(
    session: AsyncSession, telegram_ids: Iterable[int]
) -> dict[int, User]:
    ids_list = list(telegram_ids)
    if not ids_list:
        return {}
    stmt = select(User).where(User.telegram_id.in_(ids_list))
    res = await session.execute(stmt)
    users = res.scalars().all()
    return {u.telegram_id: u for u in users}


async def get_user_by_telegram_id(
    session: AsyncSession, telegram_id: int
) -> User | None:
    res = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return res.scalar_one_or_none()


async def set_referrer_if_empty(
    session: AsyncSession, user: User, referrer_telegram_id: int
) -> None:
    if user.referred_by_user_id is not None or user.telegram_id == referrer_telegram_id:
        return
    inviter = await get_user_by_telegram_id(session, referrer_telegram_id)
    if inviter is not None:
        user.referred_by_user_id = inviter.id


async def mark_user_joined(session: AsyncSession, user: User) -> None:
    if not user.has_joined_group:
        user.has_joined_group = True


async def register_invite_on_group_join(session: AsyncSession, joined_user: User) -> bool:
    if joined_user.referred_by_user_id is None:
        return False
    inviter = await session.get(User, joined_user.referred_by_user_id)
    if inviter is None or inviter.id == joined_user.id:
        # #region agent log
        payload = {
            "sessionId": "20ebd7",
            "runId": "pre-fix",
            "hypothesisId": "H8_referral_double_counting_or_non_join_events",
            "location": "database/queries.py:register_invite_on_group_join",
            "message": "Invite registration skipped",
            "data": {
                "inviter_missing": inviter is None,
                "self_ref": inviter is not None and inviter.id == joined_user.id,
            },
            "timestamp": int(time.time() * 1000),
        }
        try:
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=False) + "\n")
        except Exception:  # noqa: BLE001
            print(
                "DEBUGLOG_WRITE_FAIL: database/queries.py:register_invite_on_group_join"
            )
        # #endregion
        return False
    invite = await increment_invite(session, inviter, joined_user, "group_join")
    return invite is not None



