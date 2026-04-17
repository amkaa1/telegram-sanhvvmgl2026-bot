from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import settings


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Профайл", callback_data="profile"),
                InlineKeyboardButton(text="Лидерборд", callback_data="leaderboard"),
            ],
            [
                InlineKeyboardButton(text="Урилга", callback_data="invite"),
            ],
        ]
    )


def open_bot_private_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Bot нээх",
                    url=f"https://t.me/{settings.bot_username}?start=activate",
                )
            ]
        ]
    )
