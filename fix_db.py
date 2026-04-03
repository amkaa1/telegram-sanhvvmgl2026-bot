import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = "postgresql+asyncpg://postgres:kxzQyhDCJtnFgJgVksZjbQvXHEGnZMZa@postgres.railway.internal:5432/railway"

async def fix():
    engine = create_async_engine(DATABASE_URL)

    async with engine.begin() as conn:
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS referred_by_user_id BIGINT;")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS invites_count INTEGER DEFAULT 0;")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS verified BOOLEAN DEFAULT FALSE;")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS has_joined_group BOOLEAN DEFAULT FALSE;")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_suspicious BOOLEAN DEFAULT FALSE;")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS reward_500_sent BOOLEAN DEFAULT FALSE;")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS reward_1000_sent BOOLEAN DEFAULT FALSE;")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS reward_2000_sent BOOLEAN DEFAULT FALSE;")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS reward_5000_sent BOOLEAN DEFAULT FALSE;")

    print("DONE ✅")

asyncio.run(fix())