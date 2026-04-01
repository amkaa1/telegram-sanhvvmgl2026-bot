import datetime as dt
from typing import Any, Callable, Dict, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import SessionLocal
from database.queries import get_or_create_user, get_recent_message_count, log_message, set_mute
from utils.logger import logger


class AntiFloodMiddleware(BaseMiddleware):
    def __init__(self, limit_messages: int = 5, per_seconds: int = 5):
        super().__init__()
        self.limit_messages = limit_messages
        self.per_seconds = per_seconds

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Message) and event.chat and event.chat.id:
            async with SessionLocal() as session:  # type: AsyncSession
                await self._check_flood(session, event)
        return await handler(event, data)

    async def _check_flood(self, session: AsyncSession, message: Message) -> None:
        if message.from_user is None:
            return
        user = await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
        )
        await log_message(session, user)
        count = await get_recent_message_count(session, user, self.per_seconds)
        if count >= self.limit_messages:
            until = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc) + dt.timedelta(
                hours=1
            )
            await set_mute(session, user, until)
            await session.commit()
            try:
                await message.chat.restrict(
                    user_id=message.from_user.id,
                    permissions={"can_send_messages": False},
                    until_date=until,
                )
                await message.answer(
                    "⛔ <b>Спам илэрлээ.</b>\n"
                    "Та 5 секундын дотор хэт олон мессеж илгээсэн тул түр хугацаанд чимээгүй боллоо."
                )
            except Exception as exc:  # noqa: BLE001
                logger.error("Failed to mute spammer: %s", exc)

