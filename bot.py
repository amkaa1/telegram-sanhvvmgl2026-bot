import asyncio

from config import settings
from database.db import engine
from database.models import Base
from loader import bot, dp
from utils.debug_log import debug_log
from utils.logger import logger, setup_logging


async def main() -> None:
    setup_logging(settings.log_level)
    # region agent log
    debug_log("run3", "H1", "bot.py:12", "startup_begin", {"has_token": bool(settings.bot_token), "group_id": settings.group_id})
    # endregion
    logger.info("Бот эхэлж байна...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as exc:
        logger.exception("DB эхлүүлэх үед алдаа гарлаа: %s", exc)
        print("Өгөгдлийн сан руу холбогдож чадсангүй. DATABASE_URL болон сүлжээний тохиргоогоо шалгана уу.")
        raise

    # region agent log
    debug_log("run3", "H1", "bot.py:23", "db_ready", {"database_url_prefix": settings.database_url.split('://')[0]})
    # endregion
    await bot.delete_webhook(drop_pending_updates=True)
    # region agent log
    debug_log("run3", "H2", "bot.py:27", "polling_start", {"update_types_count": len(dp.resolve_used_update_types())})
    # endregion
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as exc:
        logger.exception("Polling ажиллах үед алдаа гарлаа: %s", exc)
        raise
    finally:
        logger.info("Бот унтарч байна...")
        await bot.session.close()
        await engine.dispose()
        logger.info("Бот цэвэр унтарлаа.")


if __name__ == "__main__":
    asyncio.run(main())

