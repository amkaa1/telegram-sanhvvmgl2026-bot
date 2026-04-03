from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="/profile"), KeyboardButton(text="/invite")],
            [KeyboardButton(text="/leaderboard"), KeyboardButton(text="/report")],
        ],
        resize_keyboard=True,
    )
