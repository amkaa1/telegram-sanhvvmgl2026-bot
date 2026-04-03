from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import SessionLocal
from database.queries import get_or_create_user, set_referrer_if_empty
from keyboards.reply import main_menu_keyboard
from services.reputation import get_trust_level, is_verified

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    if message.from_user is None:
        return

    args = message.text.split(maxsplit=1) if message.text else []
    payload = args[1].strip() if len(args) == 2 else None

    async with SessionLocal() as session:  # type: AsyncSession
        user = await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
        )

        if payload:
            try:
                inviter_telegram_id = int(payload)
            except ValueError:
                inviter_telegram_id = None
            if inviter_telegram_id and inviter_telegram_id != message.from_user.id:
                await set_referrer_if_empty(session, user, inviter_telegram_id)

        await session.commit()

    text_lines: list[str] = []
    text_lines.append("👋 Сайн байна уу!")
    text_lines.append(
        "Энэ бол манай группийн <b>итгэлцэл, урилга, модерацийн</b> бот юм."
    )
    text_lines.append("")
    text_lines.append(
        "Хүн group-д орж ирсний дараа урилгын тоо нэмэгдэнэ. Эхлээд /invite линк ашиглана уу."
    )
    text_lines.append("")

    level = get_trust_level(user.reputation_positive)
    badge = "✔ Verified" if is_verified(user.reputation_positive) or user.verified else ""
    profile_line = f"👤 Таны түвшин: <b>{level}</b>" + (f" ({badge})" if badge else "")
    text_lines.append(profile_line)
    text_lines.append("")
    text_lines.append("Үндсэн командууд:")
    text_lines.append("• /profile – Профайл харах")
    text_lines.append("• /invite – Урилгын хувийн линк")
    text_lines.append("• /top эсвэл /leaderboard – Лидерүүд")
    text_lines.append("• /report – Гомдол илгээх")

    await message.answer("\n".join(text_lines), reply_markup=main_menu_keyboard())
