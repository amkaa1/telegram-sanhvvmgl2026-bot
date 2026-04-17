from __future__ import annotations

import asyncio

from aiogram import Bot
from aiogram.types import Message


async def safe_delete_message(bot: Bot, chat_id: int, message_id: int) -> bool:
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
        return True
    except Exception:
        return False


async def _delete_after_delay(
    bot: Bot,
    *,
    chat_id: int,
    message_id: int,
    delay_seconds: int,
) -> None:
    await asyncio.sleep(delay_seconds)
    await safe_delete_message(bot, chat_id, message_id)


def schedule_delete_message(
    bot: Bot,
    *,
    chat_id: int,
    message_id: int,
    delay_seconds: int,
) -> None:
    asyncio.create_task(
        _delete_after_delay(
            bot,
            chat_id=chat_id,
            message_id=message_id,
            delay_seconds=delay_seconds,
        )
    )


async def send_temp_message(
    message: Message,
    text: str,
    *,
    ttl_seconds: int,
    reply_markup=None,
) -> Message:
    sent = await message.answer(text, reply_markup=reply_markup)
    schedule_delete_message(
        message.bot,
        chat_id=sent.chat.id,
        message_id=sent.message_id,
        delay_seconds=ttl_seconds,
    )
    return sent
