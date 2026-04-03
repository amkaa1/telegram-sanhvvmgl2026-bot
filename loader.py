from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import ErrorEvent

from config import settings
from handlers import admin, invite, join_events, leaderboard, menu, moderation, profile, rating, report, start, stats
from middlewares.antiflood import AntiFloodMiddleware
from middlewares.logging_middleware import LoggingMiddleware
from utils.logger import logger

bot = Bot(
    token=settings.bot_token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)

dp = Dispatcher()
dp.message.middleware(LoggingMiddleware())
dp.message.middleware(AntiFloodMiddleware())

dp.include_router(start.router)
dp.include_router(menu.router)
dp.include_router(invite.router)
dp.include_router(profile.router)
dp.include_router(leaderboard.router)
dp.include_router(rating.router)
dp.include_router(report.router)
dp.include_router(admin.router)
dp.include_router(moderation.router)
dp.include_router(stats.router)
dp.include_router(join_events.router)


@dp.error()
async def on_global_error(event: ErrorEvent) -> None:
    logger.exception("Глобал алдаа: %s", event.exception)
    upd = event.update
    if upd.message:
        await upd.message.answer("Системийн алдаа гарлаа. Түр хүлээгээд дахин оролдоно уу.")
    elif upd.callback_query and upd.callback_query.message:
        await upd.callback_query.answer("Системийн алдаа.", show_alert=True)


__all__ = ["bot", "dp"]

if __name__ == "__main__":
    raise SystemExit("loader.py-г шууд ажиллуулахгүй. Ботыг `python bot.py` командаар ажиллуулна уу.")
