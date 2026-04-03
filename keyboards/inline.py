from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import settings


def group_join_inline_keyboard() -> InlineKeyboardMarkup | None:
    url = settings.group_invite_link
    if not url:
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Группд нэгдэх", url=url)]
        ]
    )


def report_reason_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Scam", callback_data="report:scam")],
            [InlineKeyboardButton(text="Spam", callback_data="report:spam")],
            [InlineKeyboardButton(text="Fake account", callback_data="report:fake")],
        ]
    )
