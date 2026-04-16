from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


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
