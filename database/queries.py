import datetime as dt
import secrets
from typing import Iterable, Sequence

from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    Invite,
    MessageLog,
    Mute,
    Rating,
    RatingUndoToken,
    Report,
    User,
    UsernameHistory,
    Warning,
)
from utils.logger import logger


RATING_LIMIT_COUNT = 2
RATING_LIMIT_HOURS = 72
RATING_UNDO_SECONDS = 10


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
        now = dt.datetime.now(dt.timezone.utc)
        if username is not None and user.username != username:
            session.add(
                UsernameHistory(
                    user_id=user.id,
                    old_username=user.username,
                    new_username=username,
                )
            )
            user.username = username
            updated = True
        if first_name is not None and user.first_name != first_name:
            user.first_name = first_name
            updated = True
        if last_name is not None and user.last_name != last_name:
            user.last_name = last_name
            updated = True
        if user.last_seen_at != now:
            user.last_seen_at = now
            updated = True
        if updated:
            await session.flush()
        return user
    now = dt.datetime.now(dt.timezone.utc)
    user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        is_bot=False,
        first_seen_at=now,
        last_seen_at=now,
    )
    session.add(user)
    await session.flush()
    return user


def _rating_window_key(now: dt.datetime) -> str:
    if now.tzinfo is None:
        now = now.replace(tzinfo=dt.timezone.utc)
    return f"r{int(now.timestamp() * 1000000)}"


async def can_rate_user(
    session: AsyncSession, from_user: User, to_user: User
) -> bool:
    if from_user.id == to_user.id:
        return False
    now = dt.datetime.now(dt.timezone.utc)
    cutoff = now - dt.timedelta(hours=RATING_LIMIT_HOURS)
    stmt = select(func.count(Rating.id)).where(
        and_(
            Rating.from_user_id == from_user.id,
            Rating.created_at >= cutoff,
            Rating.undone_at.is_(None),
        )
    )
    res = await session.execute(stmt)
    return int(res.scalar_one() or 0) < RATING_LIMIT_COUNT


async def add_rating(
    session: AsyncSession,
    from_user: User,
    to_user: User,
    is_positive: bool,
    *,
    source_chat_type: str | None = None,
    source_chat_id: int | None = None,
    source_message_id: int | None = None,
) -> Rating | None:
    if from_user.id == to_user.id:
        return None

    now = dt.datetime.now(dt.timezone.utc)
    window_key = _rating_window_key(now)

    # new rating
    rating = Rating(
        from_user_id=from_user.id,
        to_user_id=to_user.id,
        is_positive=is_positive,
        rating_type="good" if is_positive else "bad",
        created_window=window_key,
        source_chat_type=source_chat_type,
        source_chat_id=source_chat_id,
        source_message_id=source_message_id,
    )
    session.add(rating)
    try:
        if is_positive:
            to_user.reputation_positive += 1
        else:
            to_user.reputation_negative += 1
        await session.flush()
    except IntegrityError:
        await session.rollback()
        logger.exception(
            "add_rating integrity_error actor_user_id=%s target_user_id=%s action=%s",
            from_user.id,
            to_user.id,
            "good" if is_positive else "bad",
        )
        return None
    except Exception:
        logger.exception(
            "add_rating failed actor_user_id=%s target_user_id=%s action=%s",
            from_user.id,
            to_user.id,
            "good" if is_positive else "bad",
        )
        raise
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
        logger.info(
            "duplicate join skipped: invite row exists inviter_id=%s invited_id=%s",
            inviter.id,
            invited.id,
        )
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
        logger.info(
            "duplicate join skipped: integrity race inviter_id=%s invited_id=%s",
            inviter.id,
            invited.id,
        )
        return None
    inviter.invites_count += 1
    await session.flush()
    return invite


async def add_report(
    session: AsyncSession,
    reporter: User,
    reported: User,
    reason: str,
    *,
    evidence_text: str | None = None,
    evidence_file_id: str | None = None,
    evidence_type: str | None = None,
) -> Report:
    report = Report(
        reporter_id=reporter.id,
        reported_user_id=reported.id,
        reason=reason,
        status="pending",
        evidence_text=evidence_text,
        evidence_file_id=evidence_file_id,
        evidence_type=evidence_type,
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


async def get_user_by_username(
    session: AsyncSession, username: str
) -> User | None:
    uname = username.lstrip("@").strip()
    if not uname:
        return None
    res = await session.execute(select(User).where(User.username == uname))
    return res.scalar_one_or_none()


async def set_referrer_if_empty(
    session: AsyncSession, user: User, referrer_telegram_id: int
) -> str:
    """Returns outcome: saved | ignored_self | ignored_already_set."""
    if user.telegram_id == referrer_telegram_id:
        logger.info(
            "referral ignored: self_ref user_telegram_id=%s", user.telegram_id
        )
        return "ignored_self"
    if user.referred_by_user_id is not None:
        logger.info(
            "referral ignored: already_set user_telegram_id=%s", user.telegram_id
        )
        return "ignored_already_set"
    inviter = await get_or_create_user(
        session,
        telegram_id=referrer_telegram_id,
        username=None,
        first_name=None,
        last_name=None,
    )
    user.referred_by_user_id = inviter.id
    logger.info(
        "referral saved user_telegram_id=%s inviter_telegram_id=%s",
        user.telegram_id,
        referrer_telegram_id,
    )
    return "saved"


async def mark_bot_private_started(session: AsyncSession, user: User) -> None:
    user.bot_private_started = True
    user.last_seen_at = dt.datetime.now(dt.timezone.utc)
    await session.flush()


async def count_recent_ratings(
    session: AsyncSession, *, actor_user_id: int, hours: int = RATING_LIMIT_HOURS
) -> int:
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=hours)
    stmt = select(func.count(Rating.id)).where(
        and_(
            Rating.from_user_id == actor_user_id,
            Rating.created_at >= cutoff,
            Rating.undone_at.is_(None),
        )
    )
    return int((await session.execute(stmt)).scalar_one() or 0)


async def get_rating_cooldown_remaining(
    session: AsyncSession, *, actor_user_id: int
) -> dt.timedelta | None:
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=RATING_LIMIT_HOURS)
    stmt = (
        select(Rating.created_at)
        .where(
            and_(
                Rating.from_user_id == actor_user_id,
                Rating.created_at >= cutoff,
                Rating.undone_at.is_(None),
            )
        )
        .order_by(Rating.created_at.asc())
    )
    rows = (await session.execute(stmt)).scalars().all()
    if len(rows) < RATING_LIMIT_COUNT:
        return None
    unlock_at = rows[0] + dt.timedelta(hours=RATING_LIMIT_HOURS)
    remaining = unlock_at - dt.datetime.now(dt.timezone.utc)
    if remaining.total_seconds() <= 0:
        return None
    return remaining


async def create_rating_undo_token(
    session: AsyncSession, *, rating_id: int, actor_telegram_id: int
) -> RatingUndoToken:
    token = secrets.token_urlsafe(24)
    undo = RatingUndoToken(
        rating_id=rating_id,
        actor_telegram_id=actor_telegram_id,
        token=token,
        expires_at=dt.datetime.now(dt.timezone.utc)
        + dt.timedelta(seconds=RATING_UNDO_SECONDS),
    )
    session.add(undo)
    await session.flush()
    return undo


async def undo_rating_by_token(
    session: AsyncSession, *, token: str, actor_telegram_id: int
) -> str:
    now = dt.datetime.now(dt.timezone.utc)
    res = await session.execute(
        select(RatingUndoToken).where(RatingUndoToken.token == token)
    )
    undo = res.scalar_one_or_none()
    if undo is None or undo.actor_telegram_id != actor_telegram_id:
        return "not_found"
    if undo.used_at is not None:
        return "already_used"
    if undo.expires_at < now:
        return "expired"
    rating = await session.get(Rating, undo.rating_id)
    if rating is None or rating.undone_at is not None:
        undo.used_at = now
        await session.flush()
        return "already_used"
    target_user = await session.get(User, rating.to_user_id)
    if target_user is None:
        return "not_found"
    if rating.is_positive:
        target_user.reputation_positive = max(0, target_user.reputation_positive - 1)
    else:
        target_user.reputation_negative = max(0, target_user.reputation_negative - 1)
    rating.undone_at = now
    undo.used_at = now
    await session.flush()
    return "ok"


async def get_approved_report_count(session: AsyncSession, user_id: int) -> int:
    stmt = select(func.count(Report.id)).where(
        and_(Report.reported_user_id == user_id, Report.status == "approved")
    )
    return int((await session.execute(stmt)).scalar_one() or 0)


async def update_report_status(
    session: AsyncSession,
    *,
    report_id: int,
    status: str,
    admin_telegram_id: int,
) -> Report | None:
    report = await session.get(Report, report_id)
    if report is None:
        return None
    report.status = status
    report.reviewed_at = dt.datetime.now(dt.timezone.utc)
    report.reviewed_by_admin_id = admin_telegram_id
    await session.flush()
    return report


async def mark_user_joined(session: AsyncSession, user: User) -> None:
    if not user.has_joined_group:
        user.has_joined_group = True


async def register_invite_on_group_join(session: AsyncSession, joined_user: User) -> bool:
    if joined_user.referral_join_counted:
        logger.info(
            "duplicate join skipped: already_counted_flag joined_user_id=%s",
            joined_user.id,
        )
        return False
    if joined_user.referred_by_user_id is None:
        logger.info(
            "join count skipped: no_referred_by joined_user_id=%s", joined_user.id
        )
        return False
    inviter = await session.get(User, joined_user.referred_by_user_id)
    if inviter is None or inviter.id == joined_user.id:
        logger.warning(
            "join count skipped: bad inviter joined_user_id=%s inviter_missing=%s",
            joined_user.id,
            inviter is None,
        )
        return False
    invite = await increment_invite(session, inviter, joined_user, "group_join")
    now = dt.datetime.now(dt.timezone.utc)
    if invite is not None:
        joined_user.referral_join_counted = True
        joined_user.referral_counted_at = now
        logger.info(
            "join counted joined_user_id=%s inviter_id=%s",
            joined_user.id,
            inviter.id,
        )
        return True
    joined_user.referral_join_counted = True
    joined_user.referral_counted_at = joined_user.referral_counted_at or now
    logger.info(
        "duplicate join skipped: invite_row_exists joined_user_id=%s inviter_id=%s",
        joined_user.id,
        inviter.id,
    )
    return False



