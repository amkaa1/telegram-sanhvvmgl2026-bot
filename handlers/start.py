from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import SessionLocal
from database.queries import get_or_create_user, set_referrer_if_empty
from keyboards.inline import (
    CALLBACK_START_CMDS,
    CALLBACK_START_INVITE,
    CALLBACK_START_REWARD,
    CALLBACK_START_RULES,
    group_join_inline_keyboard,
    start_info_inline_keyboard,
)
from keyboards.reply import main_menu_keyboard
from services.invite_tracker import parse_start_referral_payload
from services.reputation import get_trust_level, is_verified
from utils.start_sections import (
    section_commands,
    section_invite_growth,
    section_reward_system,
    section_rules_and_trust,
)

router = Router()

_START_SECTION_HANDLERS = {
    CALLBACK_START_RULES: section_rules_and_trust,
    CALLBACK_START_INVITE: section_invite_growth,
    CALLBACK_START_REWARD: section_reward_system,
    CALLBACK_START_CMDS: section_commands,
}


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

    level = get_trust_level(user.reputation_positive)
    badge = "✔ Verified" if is_verified(user.reputation_positive) or user.verified else ""
    profile_line = f"👤 Таны одоогийн түвшин: <b>{level}</b>" + (
        f" ({badge})" if badge else ""
    )

    text_lines: list[str] = [
    "👋 Сайн байна уу!",
    "Санхүү 2026 — хамгийн найдвартай охидуудтай хүчтэй Invite & Trust system-тэй community-д тавтай морил 🚀",
    "Идэвхтэй оролцож, reputation өсгөж, бодит орлого олох боломжтой 💸",
    "👇 Доорх Button дээр дарж дэлгэрэнгүй мэдээлэл авна уу",
]
    await message.answer(
        "\n".join(text_lines),
        reply_markup=start_info_inline_keyboard(),
    )
    await message.answer("📱 Үндсэн доорх цэс:", reply_markup=main_menu_keyboard())

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


@router.callback_query(
    F.data.in_(
        {
            CALLBACK_START_RULES,
            CALLBACK_START_INVITE,
            CALLBACK_START_REWARD,
            CALLBACK_START_CMDS,
        }
    )
)
async def on_start_section_callback(call: CallbackQuery) -> None:
    if call.data is None or call.message is None:
        return
    builder = _START_SECTION_HANDLERS.get(call.data)
    if builder is None:
        await call.answer()
        return
    await call.answer()
    await call.message.answer(builder())


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "ℹ️ Тусламж: <code>/start</code> дээрх товчлуур болон доорх үндсэн цэснээс "
        "дүрэм, урилга, шагнал, командын мэдээллийг үзнэ үү.",
    )
