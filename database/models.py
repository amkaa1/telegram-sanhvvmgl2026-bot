from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc)
    )
    reputation_positive: Mapped[int] = mapped_column(Integer, default=0)
    reputation_negative: Mapped[int] = mapped_column(Integer, default=0)
    invites_count: Mapped[int] = mapped_column(Integer, default=0)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    referred_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    referral_join_counted: Mapped[bool] = mapped_column(Boolean, default=False)
    referral_counted_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    has_joined_group: Mapped[bool] = mapped_column(Boolean, default=False)
    is_suspicious: Mapped[bool] = mapped_column(Boolean, default=False)
    reward_500_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    reward_1000_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    reward_2000_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    reward_5000_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    bot_private_started: Mapped[bool] = mapped_column(Boolean, default=False)

    ratings_given: Mapped[list["Rating"]] = relationship(
        back_populates="from_user", foreign_keys="Rating.from_user_id"
    )
    ratings_received: Mapped[list["Rating"]] = relationship(
        back_populates="to_user", foreign_keys="Rating.to_user_id"
    )


class Rating(Base):
    __tablename__ = "ratings"
    __table_args__ = (
        UniqueConstraint(
            "from_user_id", "to_user_id", "created_window", name="uix_rating_window"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    from_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    to_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    is_positive: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc)
    )
    created_window: Mapped[str] = mapped_column(String(32), index=True)

    from_user: Mapped[User] = relationship(
        back_populates="ratings_given", foreign_keys=[from_user_id]
    )
    to_user: Mapped[User] = relationship(
        back_populates="ratings_received", foreign_keys=[to_user_id]
    )


class Invite(Base):
    __tablename__ = "invites"
    __table_args__ = (
        UniqueConstraint("inviter_id", "invited_user_id", name="uix_inviter_invited_user"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    inviter_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    invited_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc)
    )
    link_hash: Mapped[str] = mapped_column(String(128), index=True)

    inviter: Mapped[User] = relationship(
        foreign_keys=[inviter_id], backref="invites_made"
    )
    invited_user: Mapped[User] = relationship(
        foreign_keys=[invited_user_id], backref="invited_by"
    )


class ReportReasonEnum(str, Enum):  # type: ignore[misc]
    SCAM = "scam"
    SPAM = "spam"
    FAKE = "fake"


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    reported_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    reason: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc)
    )


class Warning(Base):
    __tablename__ = "warnings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc)
    )


class Mute(Base):
    __tablename__ = "mutes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    until: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc)
    )


class MessageLog(Base):
    __tablename__ = "message_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc), index=True
    )


class GroupButtonThrottle(Base):
    """Per-Telegram-user limits for inline callbacks in group/supergroup chats."""

    __tablename__ = "group_button_throttles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    locked_until: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_press_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    burst_window_start: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    burst_count: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: dt.datetime.now(dt.timezone.utc),
        onupdate=lambda: dt.datetime.now(dt.timezone.utc),
    )
