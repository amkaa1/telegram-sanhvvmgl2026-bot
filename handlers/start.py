from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import SessionLocal
from database.queries import get_or_create_user, set_referrer_if_empty
from keyboards.inline import group_join_inline_keyboard
from keyboards.reply import main_menu_keyboard
from services.invite_tracker import parse_start_referral_payload
from services.reputation import get_trust_level, is_verified

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    if message.from_user is None:
        return

    args = message.text.split(maxsplit=1) if message.text else []
    payload = args[1].strip() if len(args) == 2 else None

    inviter_tid = parse_start_referral_payload(payload)
    referral_outcome: str | None = None

    async with SessionLocal() as session:  # type: AsyncSession
        user = await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
        )

        if inviter_tid is not None:
            referral_outcome = await set_referrer_if_empty(session, user, inviter_tid)

        await session.commit()

    text_lines: list[str] = []
    text_lines.append("👋 Сайн байна уу!")
    text_lines.append(
        "Монголын анхны Invite Growth & Trust System-тэй хамгийн найдвартай санхүү Group-д тавтай морилно уу."
    )
    text_lines.append("").
        ""
    )
    text_lines.append("Үндсэн командын жагсаалт:")

    level = get_trust_level(user.reputation_positive)
    badge = "✔ Verified" if is_verified(user.reputation_positive) or user.verified else ""
    profile_line = f"👤 Таны түвшин: <b>{level}</b>" + (f" ({badge})" if badge else "")
    text_lines.append(profile_line)
    text_lines.append("")
    text_lines.append("👤/profile — Таны мэдээлэл")
    text_lines.append("🔗/invite — Урилгын линк авах")
    text_lines.append("🏆/leaderboard — Шилдэг гишүүд")
    text_lines.append("⚖️/good @user — Сайн үнэлгээ өгөх") 
    text_lines.append("🚫/bad @user — Муу үнэлгээ")
    text_lines.append(" /report – Гомдол илгээх")

    await message.answer("\n".join(text_lines), reply_markup=main_menu_keyboard())

    if referral_outcome == "saved":
        ref_text = (
            "✅ <b>Таны урилга амжилттай бүртгэгдлээ.</b>\n\n"
            "Группд нэгдсэний дараа урилгын тоо нэмэгдэнэ."
        )
        kb = group_join_inline_keyboard()
        if kb is None:
            ref_text += (
                "\n\n⚠️ <i>Группын урилгын линк (GROUP_INVITE_LINK) тохируулагдаагүй байна. "
                "Админ тохируулсны дараа дахин оролдоно уу.</i>"
            )
        else:
            ref_text += "\n\nДоорх товчоор групп руу орно уу."
        await message.answer(ref_text, reply_markup=kb)
    elif referral_outcome == "ignored_already_set":
        await message.answer(
            "ℹ️ Урилгын линк дээр та дарсан байна"
        )
    elif referral_outcome == "ignored_self":
        await message.answer("⚠️ Өөрийгөө урих боломжгүй.")
