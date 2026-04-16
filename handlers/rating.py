from aiogram import Router
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import Message

from database.db import SessionLocal
from services.reputation import rate_user
from utils.messaging import notice_dm_blocked, notice_dm_sent, safe_send_dm
from utils.target_user import resolve_rating_target

router = Router()


@router.message(Command("good"))
async def cmd_good(message: Message) -> None:
    await _handle_rating(message, positive=True)


@router.message(Command("bad"))
async def cmd_bad(message: Message) -> None:
    await _handle_rating(message, positive=False)


async def _handle_rating(message: Message, *, positive: bool) -> None:
    if message.from_user is None:
        return

    target, err = await resolve_rating_target(message)
    if err:
        await message.answer(err)
        return
    if target is None:
        await message.answer(
            "<b>Хэрхэн ашиглах вэ</b>\n"
            "• Гишүүний мессеж дээр reply хийгээд <code>/good</code> эсвэл <code>/bad</code>\n"
            "• Эсвэл: <code>/good @username</code> / <code>/bad @username</code>\n"
            "• Эсвэл reply цэснээс <code>/good</code> / <code>/bad</code>"
        )
        return

    async with SessionLocal() as session:
        result = await rate_user(session, message.from_user, target, positive=positive)

    if message.chat.type == ChatType.PRIVATE:
        if result.ok and result.detail_html:
            await message.answer(result.detail_html)
        else:
            await message.answer(result.group_line)
        return

    if not result.ok:
        await message.answer(result.group_line)
        return

    sent = False
    if result.detail_html:
        sent = await safe_send_dm(
            message.bot,
            telegram_user_id=message.from_user.id,
            text=result.detail_html,
        )
    suffix = notice_dm_sent() if sent else notice_dm_blocked()
    await message.answer(f"{result.group_line}\n\n{suffix}")
