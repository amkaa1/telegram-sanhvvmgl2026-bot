from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👤 Миний профайл", callback_data="profile"),
                InlineKeyboardButton(text="🏆 Лидерүүд", callback_data="leaderboard"),
            ],
            [
                InlineKeyboardButton(text="📨 Урилгын линк", callback_data="invite"),
            ],
        ]
    )

