from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from config import settings
from database.db import SessionLocal
from handlers.invite import cmd_invite
from handlers.leaderboard import cmd_top
from handlers.profile import cmd_profile
from handlers.rating import cmd_bad, cmd_good
from keyboards.reply import (
    MAIN_MENU_BUTTON_TEXTS,
    REPLY_BTN_BAD,
    REPLY_BTN_GOOD,
    REPLY_BTN_INVITE,
    REPLY_BTN_PROFILE,
    main_menu_keyboard,
)
from services.button_limit import (
    GroupButtonGuardResult,
    answer_guard_failure,
    check_and_record_group_button_press,
    is_group_chat,
)
from utils.logger import logger

router = Router()


def _as_command_message(message: Message, command_text: str) -> Message:
    return message.model_copy(update={"text": command_text})


def _as_command_message_from_callback(call: CallbackQuery, command_text: str) -> Message:
    if call.message is None or call.from_user is None:
        raise RuntimeError("callback without message or from_user")
    # Inline callback-ийн message дээр reply_to байвал profile/rating буруу target сонгоно.
    return call.message.model_copy(
        update={
            "text": command_text,
            "from_user": call.from_user,
            "reply_to_message": None,
        }
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    await message.answer("Үндсэн цэс нээгдлээ.", reply_markup=main_menu_keyboard())


@router.message(F.text.in_(MAIN_MENU_BUTTON_TEXTS))
async def on_main_menu_button(message: Message) -> None:
    if message.text == REPLY_BTN_PROFILE:
        await cmd_profile(_as_command_message(message, "/profile"))
    elif message.text == REPLY_BTN_INVITE:
        await cmd_invite(_as_command_message(message, "/invite"))
    elif message.text == REPLY_BTN_GOOD:
        await cmd_good(_as_command_message(message, "/good"))
    elif message.text == REPLY_BTN_BAD:
        await cmd_bad(_as_command_message(message, "/bad"))


@router.callback_query(F.data.in_({"profile", "leaderboard", "invite"}))
async def on_main_menu_inline_callback(call: CallbackQuery) -> None:
    if call.data is None or call.message is None or call.from_user is None:
        return
    try:
        if is_group_chat(call.message):
            is_adm = call.from_user.id in settings.admin_ids
            async with SessionLocal() as session:
                guard = await check_and_record_group_button_press(
                    session,
                    telegram_user_id=call.from_user.id,
                    is_admin=is_adm,
                )
                if guard != GroupButtonGuardResult.OK:
                    await session.commit()
                    await answer_guard_failure(call, guard)
                    return
                await session.commit()

        await call.answer()
        if call.data == "profile":
            await cmd_profile(_as_command_message_from_callback(call, "/profile"))
        elif call.data == "leaderboard":
            await cmd_top(_as_command_message_from_callback(call, "/leaderboard"))
        elif call.data == "invite":
            await cmd_invite(_as_command_message_from_callback(call, "/invite"))
    except Exception:
        logger.exception("on_main_menu_inline_callback: алдаа")
        try:
            await call.answer("Системийн алдаа.", show_alert=True)
        except Exception:
            pass
