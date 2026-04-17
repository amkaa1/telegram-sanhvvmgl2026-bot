import datetime as dt

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, ChatPermissions, Message, ReplyKeyboardRemove, User as TgUser

from config import settings
from database.db import SessionLocal
from database.models import User
from database.queries import (
    add_report,
    add_warning,
    get_or_create_user,
    get_user_by_username,
    set_mute,
    update_report_status,
)
from keyboards.menu import open_bot_private_keyboard
from keyboards.report import (
    admin_report_review_keyboard,
    report_evidence_skip_keyboard,
    report_reason_keyboard,
)
from services.temp_message_service import send_temp_message
from services.user_registry import ensure_user_registered, has_private_started
from utils.messaging import safe_send_dm


router = Router()


class ReportFlow(StatesGroup):
    waiting_reason = State()
    waiting_evidence = State()


def _user_label(user: TgUser) -> str:
    if user.username:
        return f"@{user.username}"
    full = " ".join(filter(None, [user.first_name, user.last_name])).strip()
    return full or str(user.id)


async def _resolve_target_by_arg(message: Message) -> TgUser | None:
    text = message.text or ""
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        return None
    arg = parts[1].strip()
    if not arg:
        return None
    if arg.startswith("@"):
        uname = arg.lstrip("@")
        async with SessionLocal() as session:
            db_user = await get_user_by_username(session, uname)
            if db_user:
                return TgUser(
                    id=db_user.telegram_id,
                    is_bot=db_user.is_bot,
                    first_name=db_user.first_name or "",
                    last_name=db_user.last_name,
                    username=db_user.username,
                )
        try:
            chat = await message.bot.get_chat(arg)
        except Exception:
            return None
        if chat.type != ChatType.PRIVATE or getattr(chat, "is_bot", False):
            return None
        return TgUser(
            id=int(chat.id),
            is_bot=False,
            first_name=getattr(chat, "first_name", "") or "",
            last_name=getattr(chat, "last_name", None),
            username=getattr(chat, "username", None),
        )
    return None


async def _ensure_group_activation(message: Message) -> bool:
    if message.from_user is None:
        return False
    if message.chat.type not in {ChatType.GROUP, ChatType.SUPERGROUP}:
        return True
    async with SessionLocal() as session:
        ok = await has_private_started(session, message.from_user)
        await session.commit()
    if ok:
        return True
    await send_temp_message(
        message,
        "🔒 Bot ашиглахын тулд эхлээд private chat дээр /start дарна уу 🔒",
        ttl_seconds=15,
        reply_markup=open_bot_private_keyboard(),
    )
    return False


async def _start_report_dm(
    message: Message,
    *,
    state: FSMContext,
    target: TgUser,
) -> None:
    if message.from_user is None:
        return
    await state.set_state(ReportFlow.waiting_reason)
    await state.update_data(
        target_user_id=target.id,
        target_username=target.username,
        target_first_name=target.first_name,
        target_last_name=target.last_name,
    )
    sent = await safe_send_dm(
        message.bot,
        telegram_user_id=message.from_user.id,
        text=(
            f"⚠️ Report эхэллээ: {_user_label(target)}\n\n"
            "Шалтгаанаа сонгоно уу:"
        ),
        reply_markup=report_reason_keyboard(),
    )
    if not sent and message.chat.type in {ChatType.GROUP, ChatType.SUPERGROUP}:
        await send_temp_message(
            message,
            "⚠️ DM рүү илгээж чадсангүй. Private chat дээр /start дарна уу ⚠️",
            ttl_seconds=10,
        )


@router.message(Command("report"))
async def cmd_report(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return
    if not await _ensure_group_activation(message):
        return

    target: TgUser | None = None
    if message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user
    if target is None:
        target = await _resolve_target_by_arg(message)

    if target is None:
        if message.chat.type in {ChatType.GROUP, ChatType.SUPERGROUP}:
            await send_temp_message(
                message,
                "⚠️ Report хийх бол тухайн хэрэглэгчийн мессеж дээр reply хийгээрэй ⚠️",
                ttl_seconds=10,
            )
        else:
            await message.answer(
                "⚠️ Report хийх хэрэглэгчээ /report @username гэж заана уу ⚠️",
                reply_markup=ReplyKeyboardRemove(),
            )
        return
    if target.is_bot or target.id == message.from_user.id:
        await message.answer("⚠️ Энэ хэрэглэгч дээр report үүсгэх боломжгүй ⚠️")
        return

    if message.chat.type in {ChatType.GROUP, ChatType.SUPERGROUP}:
        await send_temp_message(
            message,
            "⚠️ Report үргэлжлүүлэх зааврыг DM рүү илгээлээ ⚠️",
            ttl_seconds=10,
        )
    await _start_report_dm(message, state=state, target=target)


@router.message(
    F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}),
    F.text.in_({"⚠️ Report", "🚨 Report"}),
)
async def menu_report(message: Message, state: FSMContext) -> None:
    pseudo = message.model_copy(update={"text": "/report"})
    await cmd_report(pseudo, state)


@router.message(
    F.chat.type == ChatType.PRIVATE,
    F.text.in_({"⚠️ Report", "🚨 Report"}),
)
async def private_stale_menu_report(message: Message, state: FSMContext) -> None:
    # Handles old cached private reply keyboards without silent failure.
    pseudo = message.model_copy(update={"text": "/report"})
    await cmd_report(pseudo, state)


@router.callback_query(F.data.startswith("report_reason:"))
async def report_reason_callback(call: CallbackQuery, state: FSMContext) -> None:
    if call.from_user is None or call.data is None:
        return
    if await state.get_state() != ReportFlow.waiting_reason.state:
        await call.answer("Энэ report үйлдэл хүчингүй болсон байна.", show_alert=True)
        return
    reason = call.data.split(":", maxsplit=1)[1].strip()
    await state.update_data(reason=reason)
    await state.set_state(ReportFlow.waiting_evidence)
    await call.answer()
    if call.message:
        await call.message.answer(
            "Нотолгоогоо оруулна уу (текст, зураг, линк, forward). Алгасах бол товч дарна уу.",
            reply_markup=report_evidence_skip_keyboard(),
        )


@router.callback_query(F.data == "report_evidence:skip")
async def report_skip_evidence_callback(call: CallbackQuery, state: FSMContext) -> None:
    if call.from_user is None:
        return
    if await state.get_state() != ReportFlow.waiting_evidence.state:
        await call.answer("Энэ report үйлдэл хүчингүй болсон байна.", show_alert=True)
        return
    await call.answer()
    await _finalize_report(call.message, call.from_user, state, evidence_text=None, evidence_file_id=None, evidence_type=None)


@router.message(ReportFlow.waiting_evidence)
async def report_evidence_input(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return
    evidence_text = message.text.strip() if message.text else None
    evidence_file_id = None
    evidence_type = None
    if message.photo:
        evidence_file_id = message.photo[-1].file_id
        evidence_type = "photo"
    elif message.forward_date:
        evidence_type = "forwarded"
    elif evidence_text and evidence_text.startswith(("http://", "https://")):
        evidence_type = "link"
    elif evidence_text:
        evidence_type = "text"
    await _finalize_report(
        message,
        message.from_user,
        state,
        evidence_text=evidence_text,
        evidence_file_id=evidence_file_id,
        evidence_type=evidence_type,
    )


async def _finalize_report(
    message_like: Message | None,
    actor: TgUser,
    state: FSMContext,
    *,
    evidence_text: str | None,
    evidence_file_id: str | None,
    evidence_type: str | None,
) -> None:
    if message_like is None:
        return
    data = await state.get_data()
    await state.clear()
    target_id = data.get("target_user_id")
    reason = data.get("reason")
    if not target_id or not reason:
        if message_like:
            await message_like.answer("⚠️ Report хугацаа дууссан байна. Дахин эхлүүлнэ үү ⚠️")
        return
    target = TgUser(
        id=int(target_id),
        is_bot=False,
        first_name=data.get("target_first_name") or "",
        last_name=data.get("target_last_name"),
        username=data.get("target_username"),
    )
    async with SessionLocal() as session:
        reporter = await ensure_user_registered(session, actor)
        reported = await get_or_create_user(
            session,
            telegram_id=target.id,
            username=target.username,
            first_name=target.first_name,
            last_name=target.last_name,
        )
        report = await add_report(
            session,
            reporter,
            reported,
            reason=reason,
            evidence_text=evidence_text,
            evidence_file_id=evidence_file_id,
            evidence_type=evidence_type,
        )
        await session.commit()

    if message_like:
        await message_like.answer("✅ Report бүртгэгдлээ. Админ шалгаж шийднэ ✅")

    admin_text = "\n".join(
        [
            "🚨 <b>Шинэ report</b>",
            f"Reporter: {_user_label(actor)} (<code>{actor.id}</code>)",
            f"Target: {_user_label(target)} (<code>{target.id}</code>)",
            f"Reason: {reason}",
            f"Evidence type: {evidence_type or 'none'}",
            f"Evidence: {evidence_text or '-'}",
            f"At: {dt.datetime.now(dt.timezone.utc).isoformat()}",
        ]
    )
    for admin_id in settings.admin_ids:
        try:
            await message_like.bot.send_message(
                admin_id,
                admin_text,
                reply_markup=admin_report_review_keyboard(report.id),
                disable_notification=True,
            )
        except Exception:
            continue


@router.callback_query(F.data.startswith("report_review:"))
async def report_review_callback(call: CallbackQuery) -> None:
    if call.from_user is None or call.data is None:
        return
    if call.from_user.id not in settings.admin_ids:
        await call.answer("Энэ үйлдэл зөвхөн админд зориулагдсан.", show_alert=True)
        return
    parts = call.data.split(":")
    if len(parts) != 3:
        await call.answer("Буруу callback формат.", show_alert=True)
        return
    report_id = int(parts[1])
    action = parts[2]

    async with SessionLocal() as session:
        report = await update_report_status(
            session,
            report_id=report_id,
            status="approved" if action == "approve" else ("rejected" if action == "reject" else "pending"),
            admin_telegram_id=call.from_user.id,
        )
        if report is None:
            await session.commit()
            await call.answer("Report олдсонгүй.", show_alert=True)
            return
        target = await session.get(User, report.reported_user_id)
        if target is None:
            await session.commit()
            await call.answer("Target олдсонгүй.", show_alert=True)
            return
        if action == "verify":
            target.manual_badge_override = "Verified"
            target.verified = True
        elif action == "unverify":
            target.manual_badge_override = None
            target.verified = False
        elif action == "warn":
            await add_warning(session, target, "Report review warning")
        elif action == "mute1d":
            until = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1)
            await set_mute(session, target, until)
        await session.commit()

    if action in {"ban", "mute1d", "warn"}:
        try:
            if action == "ban":
                await call.bot.ban_chat_member(settings.group_id, target.telegram_id)
            elif action == "mute1d":
                until = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1)
                await call.bot.restrict_chat_member(
                    settings.group_id,
                    target.telegram_id,
                    permissions=ChatPermissions(can_send_messages=False),
                    until_date=until,
                )
        except Exception:
            pass
    await call.answer("✅ Admin review бүртгэгдлээ ✅", show_alert=True)

