from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from database.db import SessionLocal
from database.queries import undo_rating_by_token
from keyboards.menu import open_bot_private_keyboard
from keyboards.reply import REPLY_BTN_BAD, REPLY_BTN_GOOD
from keyboards.report import rating_undo_keyboard
from services.reputation import rate_user
from services.temp_message_service import schedule_delete_message, send_temp_message
from services.user_registry import ensure_user_registered, has_private_started
from utils.messaging import safe_send_dm
from utils.target_user import resolve_rating_target

router = Router()


@router.message(Command("good"))
async def cmd_good(message: Message) -> None:
    await handle_rating(message, positive=True)


@router.message(Command("bad"))
async def cmd_bad(message: Message) -> None:
    await handle_rating(message, positive=False)


@router.message(
    F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}),
    F.text.in_({REPLY_BTN_GOOD, "🔥 Good", "🔥 good"}),
)
async def menu_good(message: Message) -> None:
    pseudo = message.model_copy(update={"text": "/good"})
    await handle_rating(pseudo, positive=True)


@router.message(
    F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}),
    F.text.in_({REPLY_BTN_BAD, "❌ Bad", "❌ bad"}),
)
async def menu_bad(message: Message) -> None:
    pseudo = message.model_copy(update={"text": "/bad"})
    await handle_rating(pseudo, positive=False)


@router.message(
    F.chat.type == ChatType.PRIVATE,
    F.text.in_({REPLY_BTN_GOOD, "🔥 Good", "🔥 good"}),
)
async def private_stale_menu_good(message: Message) -> None:
    # Users may still have an old reply keyboard cached in private chat.
    pseudo = message.model_copy(update={"text": "/good"})
    await handle_rating(pseudo, positive=True)


@router.message(
    F.chat.type == ChatType.PRIVATE,
    F.text.in_({REPLY_BTN_BAD, "❌ Bad", "❌ bad"}),
)
async def private_stale_menu_bad(message: Message) -> None:
    # Users may still have an old reply keyboard cached in private chat.
    pseudo = message.model_copy(update={"text": "/bad"})
    await handle_rating(pseudo, positive=False)


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
    schedule_delete_message(
        message.bot,
        chat_id=message.chat.id,
        message_id=message.message_id,
        delay_seconds=10,
    )
    return False


async def handle_rating(message: Message, *, positive: bool) -> None:
    if message.from_user is None:
        return

    if not await _ensure_group_activation(message):
        return

    target, err = await resolve_rating_target(message)
    if err:
        if message.chat.type in {ChatType.GROUP, ChatType.SUPERGROUP}:
            await send_temp_message(message, err, ttl_seconds=10)
        else:
            await message.answer(err)
        return
    if target is None:
        if message.chat.type in {ChatType.GROUP, ChatType.SUPERGROUP}:
            warning_text = (
                "⚠️ good үнэлгээ өгөх бол тухайн хэрэглэгчийн мессеж дээр reply хийгээрэй ⚠️"
                if positive
                else "⚠️ bad үнэлгээ өгөх бол тухайн хэрэглэгчийн мессеж дээр reply хийгээрэй ⚠️"
            )
            await send_temp_message(message, warning_text, ttl_seconds=10)
        else:
            await message.answer(
                "⚠️ Хэрэглэгч дээр reply хийгээд эсвэл /good @username, /bad @username ашиглана уу ⚠️",
                reply_markup=ReplyKeyboardRemove(),
            )
        return

    async with SessionLocal() as session:
        await ensure_user_registered(session, message.from_user)
        result = await rate_user(
            session,
            message.from_user,
            target,
            positive=positive,
            source_message=message,
        )

    if message.chat.type == ChatType.PRIVATE:
        if not result.ok:
            await message.answer(result.group_line, reply_markup=ReplyKeyboardRemove())
            return
        await message.answer(
            result.dm_line or result.group_line,
            reply_markup=rating_undo_keyboard(result.undo_token) if result.undo_token else None,
        )
        return

    if not result.ok:
        await send_temp_message(message, result.group_line, ttl_seconds=10)
        return

    schedule_delete_message(
        message.bot,
        chat_id=message.chat.id,
        message_id=message.message_id,
        delay_seconds=10,
    )
    await send_temp_message(message, result.group_line, ttl_seconds=10)
    if result.dm_line:
        await safe_send_dm(
            message.bot,
            telegram_user_id=message.from_user.id,
            text=result.dm_line,
            reply_markup=rating_undo_keyboard(result.undo_token) if result.undo_token else None,
        )


@router.callback_query(F.data.startswith("rating_undo:"))
async def undo_rating_callback(call: CallbackQuery) -> None:
    if call.from_user is None or call.data is None:
        return
    token = call.data.split(":", maxsplit=1)[1].strip()
    async with SessionLocal() as session:
        status = await undo_rating_by_token(
            session,
            token=token,
            actor_telegram_id=call.from_user.id,
        )
        await session.commit()
    if status == "ok":
        await call.answer("✅ Үнэлгээг буцаалаа ✅", show_alert=True)
        try:
            if call.message:
                await call.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        return
    if status == "expired":
        await call.answer("⏳ Undo хугацаа дууссан байна ⏳", show_alert=True)
        return
    await call.answer("⚠️ Энэ undo үйлдэл хүчингүй байна ⚠️", show_alert=True)
