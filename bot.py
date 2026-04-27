import asyncio

from config import settings
from database.db import engine
from database.migrations import run_safe_migrations
from database.models import Base
from loader import bot, dp
from utils.logger import logger, setup_logging


async def main() -> None:
    setup_logging(settings.log_level)
    logger.info("Бот эхэлж байна...")
    logger.info(
        "GROUP_INVITE_LINK: %s",
        "тохируулагдсан" if settings.group_invite_link else "тохируулагдаагүй",
    )
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await run_safe_migrations(conn)
    except Exception as exc:
        logger.exception("DB эхлүүлэх үед алдаа гарлаа: %s", exc)
        print("Өгөгдлийн сан руу холбогдож чадсангүй. DATABASE_URL болон сүлжээний тохиргоогоо шалгана уу.")
        raise

    await bot.delete_webhook(drop_pending_updates=True)
    try:
        # Явцад шаардлагатай update-уудыг тодорхой зааж өгнө (resolve_used_update_types()
        # зарим тохиолдолд callback_query/chat_member алдагдуулж болно).
        await dp.start_polling(
            bot,
            allowed_updates=[
                "message",
                "callback_query",
                "chat_member",
                "my_chat_member",
            ],
        )
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
