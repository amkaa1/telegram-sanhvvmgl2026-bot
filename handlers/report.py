from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database.db import SessionLocal
from database.queries import add_report, get_or_create_user


router = Router()


@router.message(Command("report"))
async def cmd_report(message: Message) -> None:
    if message.from_user is None:
        return

    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.answer(
            "🚨 Гомдол илгээхийн тулд тухайн гишүүний мессеж дээр reply хийгээд /report гэж бичнэ үү."
        )
        return

    target = message.reply_to_message.from_user
    reason_text = (
        message.text.split(maxsplit=1)[1].strip()
        if message.text and len(message.text.split(maxsplit=1)) == 2
        else ""
    )

    if not reason_text:
        reason_text = "Бусад (тайлбар оруулаагүй)"

    async with SessionLocal() as session:  # type: AsyncSession
        reporter = await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
        )
        reported = await get_or_create_user(
            session,
            telegram_id=target.id,
            username=target.username,
            first_name=target.first_name,
            last_name=target.last_name,
        )

        await add_report(session, reporter, reported, reason_text)
        await session.commit()

    await message.answer(
        "✅ Таны гомдлыг хүлээн авлаа. Админууд хянаж шийдвэрлэх болно."
    )

    text = (
        "🚨 <b>Шинэ гомдол ирлээ</b>\n\n"
        f"👤 Гомдол гаргагч: <a href=\"tg://user?id={message.from_user.id}\">{message.from_user.full_name}</a>\n"
        f"👥 Гомдол гарсан гишүүн: <a href=\"tg://user?id={target.id}\">{target.full_name}</a>\n"
        f"💬 Шалтгаан: {reason_text}"
    )
    for admin_id in settings.admin_ids:
        try:
            await message.bot.send_message(admin_id, text)
        except Exception:
            continue

