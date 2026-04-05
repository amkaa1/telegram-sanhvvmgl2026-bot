from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from handlers.invite import cmd_invite
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

router = Router()


def _as_command_message(message: Message, command_text: str) -> Message:
    return message.model_copy(update={"text": command_text})


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
