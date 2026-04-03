from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def report_reason_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Scam", callback_data="report:scam")],
            [InlineKeyboardButton(text="Spam", callback_data="report:spam")],
            [InlineKeyboardButton(text="Fake account", callback_data="report:fake")],
        ]
    )
