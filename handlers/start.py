from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database.db import SessionLocal
from database.queries import get_or_create_user, mark_bot_private_started, set_referrer_if_empty
from keyboards.inline import (
    CALLBACK_START_BACK,
    CALLBACK_START_CMDS,
    CALLBACK_START_INVITE,
    CALLBACK_START_REWARD,
    CALLBACK_START_RULES,
    group_join_inline_keyboard,
    start_back_inline_keyboard,
    start_info_inline_keyboard,
)
from keyboards.reply import main_menu_keyboard
from services.invite_tracker import parse_start_referral_payload
from utils.messaging import notice_callback_expired
from utils.start_sections import (
    help_full_text,
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

PRIVATE_WELCOME_HTML = (
    "<b>Сайн байна уу.</b>\n\n"
    "Энэ bot нь группын <b>Trust</b>, <b>профайл</b>, <b>урилга</b>, "
    "<b>лидерборд</b> зэргийг нэг дор харахад тусална.\n\n"
    "Доорх товчлуураас дүрэм, invite, шагналын тайлбарыг нээгээд үзээрэй. "
    "Командуудыг <code>/help</code>-аар шууд харж болно.\n\n"
    "Групп дээрх зарим үр дүн <b>товч</b> харагдаж, дэлгэрэнгүй нь ихэвчлэн "
    "энэ хувийн чат руу илгээгдэнэ."
)


@router.message(CommandStart(), F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
async def cmd_start_group(message: Message) -> None:
    await message.answer(
        "Энэ bot-ын бүрэн цэс, тайлбарыг <b>хувийн чат</b> дээр ашиглана уу.\n\n"
        f"@{settings.bot_username} → <code>/start</code>"
    )


@router.message(CommandStart(), F.chat.type == ChatType.PRIVATE)
async def cmd_start_private(message: Message) -> None:
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
        await mark_bot_private_started(session, user)

        if inviter_tid is not None:
            referral_outcome = await set_referrer_if_empty(session, user, inviter_tid)

        await session.commit()

    await message.answer(
        PRIVATE_WELCOME_HTML,
        reply_markup=start_info_inline_keyboard(),
    )
    await message.answer("Үндсэн цэс:", reply_markup=main_menu_keyboard())

    if referral_outcome == "saved":
        ref_text = (
            "✅ <b>Урилга бүртгэгдлээ.</b>\n\n"
            "Группд нэгдсэний дараа урилгын тоо нэмэгдэнэ."
        )
        kb = group_join_inline_keyboard()
        if kb is None:
            ref_text += (
                "\n\n⚠️ <i>GROUP_INVITE_LINK тохируулагдаагүй байна. "
                "Админ тохируулсны дараа дахин оролдоно уу.</i>"
            )
        else:
            ref_text += "\n\nДоорх товчоор групп руу орно уу."
        await message.answer(ref_text, reply_markup=kb)
    elif referral_outcome == "ignored_already_set":
        await message.answer("ℹ️ Урилгын холбоосыг өмнө нь ашигласан байна.")
    elif referral_outcome == "ignored_self":
        await message.answer("⚠️ Өөрийгөө урих боломжгүй.")


@router.callback_query(F.data == CALLBACK_START_BACK)
async def on_start_back_callback(call: CallbackQuery) -> None:
    if call.message is None:
        return
    await call.answer()
    try:
        await call.message.edit_text(
            PRIVATE_WELCOME_HTML,
            reply_markup=start_info_inline_keyboard(),
        )
    except TelegramBadRequest as exc:
        if "message is not modified" in str(exc).lower():
            return
        await call.answer(notice_callback_expired(), show_alert=True)


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
    text = builder()
    try:
        await call.message.edit_text(
            text,
            reply_markup=start_back_inline_keyboard(),
        )
    except TelegramBadRequest as exc:
        if "message is not modified" in str(exc).lower():
            return
        try:
            await call.message.answer(text, reply_markup=start_back_inline_keyboard())
        except Exception:
            await call.answer(notice_callback_expired(), show_alert=True)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(help_full_text())
