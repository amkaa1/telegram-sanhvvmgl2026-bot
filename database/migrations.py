from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection


async def run_safe_migrations(conn: AsyncConnection) -> None:
    # users
    await conn.execute(
        text(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS referred_by_user_id INTEGER"
        )
    )
    await conn.execute(
        text("ALTER TABLE users ADD COLUMN IF NOT EXISTS invites_count INTEGER DEFAULT 0")
    )
    await conn.execute(
        text("ALTER TABLE users ADD COLUMN IF NOT EXISTS verified BOOLEAN DEFAULT FALSE")
    )
    await conn.execute(
        text(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS referral_join_counted BOOLEAN DEFAULT FALSE"
        )
    )
    await conn.execute(
        text(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS referral_counted_at TIMESTAMP WITH TIME ZONE"
        )
    )
    await conn.execute(
        text("ALTER TABLE users ADD COLUMN IF NOT EXISTS has_joined_group BOOLEAN DEFAULT FALSE")
    )
    await conn.execute(
        text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_suspicious BOOLEAN DEFAULT FALSE")
    )
    await conn.execute(
        text("ALTER TABLE users ADD COLUMN IF NOT EXISTS reward_500_sent BOOLEAN DEFAULT FALSE")
    )
    await conn.execute(
        text("ALTER TABLE users ADD COLUMN IF NOT EXISTS reward_1000_sent BOOLEAN DEFAULT FALSE")
    )
    await conn.execute(
        text("ALTER TABLE users ADD COLUMN IF NOT EXISTS reward_2000_sent BOOLEAN DEFAULT FALSE")
    )
    await conn.execute(
        text("ALTER TABLE users ADD COLUMN IF NOT EXISTS reward_5000_sent BOOLEAN DEFAULT FALSE")
    )
    await conn.execute(
        text("ALTER TABLE users ADD COLUMN IF NOT EXISTS bot_private_started BOOLEAN DEFAULT FALSE")
    )
    await conn.execute(
        text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_bot BOOLEAN DEFAULT FALSE")
    )
    await conn.execute(
        text(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS first_seen_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()"
        )
    )
    await conn.execute(
        text(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()"
        )
    )
    await conn.execute(
        text("ALTER TABLE users ADD COLUMN IF NOT EXISTS manual_badge_override VARCHAR(64)")
    )
    await conn.execute(
        text("CREATE INDEX IF NOT EXISTS ix_users_referred_by_user_id ON users (referred_by_user_id)")
    )

    # ratings
    await conn.execute(
        text("ALTER TABLE ratings ADD COLUMN IF NOT EXISTS rating_type VARCHAR(8) DEFAULT 'good'")
    )
    await conn.execute(
        text("ALTER TABLE ratings ADD COLUMN IF NOT EXISTS undone_at TIMESTAMP WITH TIME ZONE")
    )
    await conn.execute(
        text("ALTER TABLE ratings ADD COLUMN IF NOT EXISTS source_chat_type VARCHAR(16)")
    )
    await conn.execute(text("ALTER TABLE ratings ADD COLUMN IF NOT EXISTS source_chat_id BIGINT"))
    await conn.execute(
        text("ALTER TABLE ratings ADD COLUMN IF NOT EXISTS source_message_id BIGINT")
    )
    await conn.execute(
        text("CREATE INDEX IF NOT EXISTS ix_ratings_created_window ON ratings (created_window)")
    )

    # reports
    await conn.execute(
        text("ALTER TABLE reports ADD COLUMN IF NOT EXISTS status VARCHAR(16) DEFAULT 'pending'")
    )
    await conn.execute(
        text("ALTER TABLE reports ADD COLUMN IF NOT EXISTS evidence_text VARCHAR(2048)")
    )
    await conn.execute(
        text("ALTER TABLE reports ADD COLUMN IF NOT EXISTS evidence_file_id VARCHAR(255)")
    )
    await conn.execute(
        text("ALTER TABLE reports ADD COLUMN IF NOT EXISTS evidence_type VARCHAR(32)")
    )
    await conn.execute(
        text("ALTER TABLE reports ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP WITH TIME ZONE")
    )
    await conn.execute(
        text("ALTER TABLE reports ADD COLUMN IF NOT EXISTS reviewed_by_admin_id BIGINT")
    )

    # supporting tables/indexes
    await conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS group_button_throttles (
                id SERIAL PRIMARY KEY,
                telegram_user_id BIGINT UNIQUE,
                locked_until TIMESTAMP WITH TIME ZONE NULL,
                last_press_at TIMESTAMP WITH TIME ZONE NULL,
                burst_window_start TIMESTAMP WITH TIME ZONE NULL,
                burst_count INTEGER DEFAULT 0,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
            """
        )
    )
    await conn.execute(
        text(
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_group_button_throttles_telegram_user_id "
            "ON group_button_throttles (telegram_user_id)"
        )
    )

    await conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS username_history (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                old_username VARCHAR(64) NULL,
                new_username VARCHAR(64) NULL,
                changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
            """
        )
    )
    await conn.execute(
        text("CREATE INDEX IF NOT EXISTS ix_username_history_user_id ON username_history (user_id)")
    )

    await conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS rating_undo_tokens (
                id SERIAL PRIMARY KEY,
                rating_id INTEGER REFERENCES ratings(id),
                actor_telegram_id BIGINT NOT NULL,
                token VARCHAR(128) UNIQUE NOT NULL,
                expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                used_at TIMESTAMP WITH TIME ZONE NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
            """
        )
    )
    await conn.execute(
        text("CREATE UNIQUE INDEX IF NOT EXISTS ix_rating_undo_tokens_token ON rating_undo_tokens (token)")
    )
    await conn.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_rating_undo_tokens_actor_telegram_id "
            "ON rating_undo_tokens (actor_telegram_id)"
        )
    )
