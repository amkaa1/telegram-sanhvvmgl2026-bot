import json
import time
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import ErrorEvent

from config import settings
from middlewares.antiflood import AntiFloodMiddleware
from middlewares.logging_middleware import LoggingMiddleware
from utils.logger import logger

DEBUG_LOG_PATH = Path(__file__).resolve().parent / "debug-1db3d4.log"


def _debug_log(run_id: str, hypothesis_id: str, location: str, message: str, data: dict) -> None:
    try:
        payload = {
            "sessionId": "1db3d4",
            "runId": run_id,
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000),
        }
        with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass


# #region agent log
_debug_log(
    "pre-fix",
    "H1_loader_import_sequence",
    "loader.py:module_start",
    "loader module import started",
    {},
)
# #endregion

try:
    # #region agent log
    _debug_log(
        "pre-fix",
        "H2_handlers_import_failure",
        "loader.py:before_handlers_import",
        "about to import handlers package modules",
        {},
    )
    # #endregion
    from handlers import admin, invite, join_events, leaderboard, menu, moderation, profile, rating, report, start, stats
    # #region agent log
    _debug_log(
        "pre-fix",
        "H2_handlers_import_failure",
        "loader.py:after_handlers_import",
        "handlers import completed successfully",
        {},
    )
    # #endregion
except Exception as exc:
    # #region agent log
    _debug_log(
        "pre-fix",
        "H3_aiogram_symbol_import_error",
        "loader.py:handlers_import_exception",
        "handlers import raised exception",
        {"error_type": type(exc).__name__, "error": str(exc)},
    )
    # #endregion
    raise

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
