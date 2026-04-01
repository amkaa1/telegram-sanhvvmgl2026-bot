from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def admin_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📊 Статистик", callback_data="admin_stats"
                ),
                InlineKeyboardButton(
                    text="🏆 Лидерүүд", callback_data="admin_leaderboard"
                ),
            ],
        ]
    )

