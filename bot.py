import asyncio
import os

from aiohttp import web
from aiogram import Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from config import settings
from database.db import engine
from database.models import Base
from handlers import start, profile, rating, invite, leaderboard, report, admin, moderation
from loader import bot, dp
from middlewares.antiflood import AntiFloodMiddleware
from utils.logger import logger


WEBHOOK_PATH = f"/webhook/{settings.bot_token}"


async def on_startup() -> None:
    # DB init
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    webhook_base = os.getenv("WEBHOOK_BASE_URL") or os.getenv("RAILWAY_PUBLIC_DOMAIN")
    if not webhook_base:
        raise RuntimeError("WEBHOOK_BASE_URL эсвэл RAILWAY_PUBLIC_DOMAIN тохируулаагүй байна.")
    webhook_base = webhook_base.rstrip("/")
    webhook_url = f"{webhook_base}{WEBHOOK_PATH}"

    await bot.set_webhook(webhook_url)
    logger.info("Webhook set to %s", webhook_url)


def setup_routers(dispatcher: Dispatcher) -> None:
    dispatcher.include_router(start.router)
    dispatcher.include_router(profile.router)
    dispatcher.include_router(rating.router)
    dispatcher.include_router(invite.router)
    dispatcher.include_router(leaderboard.router)
    dispatcher.include_router(report.router)
    dispatcher.include_router(admin.router)
    dispatcher.include_router(moderation.router)


async def main() -> None:
    setup_routers(dp)
    dp.message.middleware(AntiFloodMiddleware())

    app = web.Application()

    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    await on_startup()

    port = int(os.getenv("PORT", "8000"))
    logger.info("Starting webhook server on port %s", port)
    await web._run_app(app, host="0.0.0.0", port=port)  # type: ignore[attr-defined]


if __name__ == "__main__":
    asyncio.run(main())

