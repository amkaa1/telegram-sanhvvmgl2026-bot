# Telegram Group Growth & Trust Bot

Production-ready Telegram group bot (aiogram v3 + PostgreSQL + async SQLAlchemy) for Railway 24/7 deployment.

## Stack
- Python 3.11+
- aiogram==3.12.0
- SQLAlchemy[asyncio]==2.0.36
- asyncpg==0.30.0
- python-dotenv==1.0.1
- PostgreSQL

## Railway Environment Variables
- `BOT_TOKEN`: BotFather token
- `BOT_USERNAME`: bot username (`my_bot`)
- `GROUP_ID`: target group chat id (`-100...`)
- `ADMIN_IDS`: comma-separated telegram ids
- `DATABASE_URL`: Railway PostgreSQL URL (`postgresql://...`)
- `LOG_LEVEL`: `INFO` / `WARNING` / `DEBUG`

`DATABASE_URL` автоматаар `postgresql+asyncpg://` хэлбэрт хөрвөнө.

## Run (local or Railway)
1. Python 3.11+ суулга
2. Dependencies:
   - `pip install -r requirements.txt`
3. `.env.example`-г `.env` болгож шаардлагатай утгуудыг бөглөнө
4. Start:
   - `python bot.py`

## Commands
- User: `/start`, `/menu`, `/invite`, `/profile`, `/leaderboard`, `/topinvite`, `/topgood`, `/topbad`, `/good`, `/bad`, `/report`
- Admin: `/admin`, `/stats`, `/ban`, `/mute`, `/unmute`, `/warn`, `/warnings`, `/verify`, `/unverify`, `/checkuser`

## Notes
- Invite зөвхөн user group-д бодитоор орж ирэхэд тоологдоно.
- Rating: 72 цагт нийт 2 үнэлгээ.
- Verified: auto + manual тусдаа хадгалагдана.
- Reward threshold бүр нэг удаа л trigger хийнэ.
