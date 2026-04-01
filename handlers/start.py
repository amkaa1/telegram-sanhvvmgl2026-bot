from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import SessionLocal
from database.models import User
from database.queries import get_or_create_user, increment_invite
from keyboards.menu import main_menu
from services.invite_tracker import build_invite_payload
from services.reputation import get_trust_level, is_verified


router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    if message.from_user is None:
        return

    args = message.text.split(maxsplit=1) if message.text else []
    payload = None
    if len(args) == 2:
        payload = args[1].strip()

    async with SessionLocal() as session:
        user = await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
        )

        text_lines: list[str] = []
        text_lines.append("👋 Сайн байна уу!")
        text_lines.append(
            "Энэ бол манай группийн <b>итгэлцэл, урилга, модерацийн</b> бот юм."
        )
        text_lines.append("")

        if payload:
            # payload нь урилга өгсөн хэрэглэгчийн ID
            try:
                inviter_telegram_id = int(payload)
            except ValueError:
                inviter_telegram_id = None

            if inviter_telegram_id and inviter_telegram_id != message.from_user.id:
                from database.queries import get_or_create_user as _get_user

                inviter = await _get_user(
                    session,
                    telegram_id=inviter_telegram_id,
                    username=None,
                    first_name=None,
                    last_name=None,
                )
                invite = await increment_invite(session, inviter, user, payload)
                if invite:
                    text_lines.append(
                        "📨 Та манай группт <b>урилгын линкээр</b> нэгдсэн байна. "
                        "Урилга илгээсэн гишүүний статистик шинэчлэгдлээ."
                    )
                await session.commit()

        level = get_trust_level(user.reputation_positive)
        badge = "✔ Verified" if is_verified(user.reputation_positive) or user.verified else ""
        profile_line = (
            f"👤 Таны түвшин: <b>{level}</b>"
            + (f" ({badge})" if badge else "")
        )
        text_lines.append(profile_line)
        text_lines.append("")
        text_lines.append("Үндсэн коммандууд:")
        text_lines.append("• /profile – Профайл харах")
        text_lines.append("• /invite – Урилгын хувийн линк")
        text_lines.append("• /top – Лидерүүдийн жагсаалт")
        text_lines.append("• /report – Гишүүний талаарх гомдол илгээх")

        await message.answer("\n".join(text_lines), reply_markup=main_menu())

