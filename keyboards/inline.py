from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import settings

CALLBACK_START_RULES = "start:rules"
CALLBACK_START_INVITE = "start:invite"
CALLBACK_START_REWARD = "start:reward"
CALLBACK_START_CMDS = "start:cmds"


def start_info_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📜 Дүрэм & Trust System",
                    callback_data=CALLBACK_START_RULES,
                )
            ],
            [
                InlineKeyboardButton(
                    text="🚀 Invite Growth System",
                    callback_data=CALLBACK_START_INVITE,
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏆 Reward System",
                    callback_data=CALLBACK_START_REWARD,
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚙️ Үндсэн коммандууд",
                    callback_data=CALLBACK_START_CMDS,
                )
            ],
        ]
    )


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
