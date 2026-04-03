from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from keyboards.reply import main_menu_keyboard

router = Router()


@router.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    await message.answer("Үндсэн цэс нээгдлээ.", reply_markup=main_menu_keyboard())
