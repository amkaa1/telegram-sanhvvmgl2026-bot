from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import settings

CALLBACK_START_RULES = "start:rules"
CALLBACK_START_INVITE = "start:invite"
CALLBACK_START_REWARD = "start:reward"
CALLBACK_START_CMDS = "start:cmds"
CALLBACK_START_BACK = "start:back"
CALLBACK_START_CLOSE = "start:close"


def start_info_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📘 Дүрэм & Trust Level",
                    callback_data=CALLBACK_START_RULES,
                ),
                InlineKeyboardButton(
                    text="📨 Invite System",
                    callback_data=CALLBACK_START_INVITE,
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎁 Reward",
                    callback_data=CALLBACK_START_REWARD,
                ),
                InlineKeyboardButton(
                    text="🧭 Командууд",
                    callback_data=CALLBACK_START_CMDS,
                )
            ],
        ]
    )


def start_back_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="← Буцах",
                    callback_data=CALLBACK_START_BACK,
                ),
                InlineKeyboardButton(
                    text="✖️ Хаах",
                    callback_data=CALLBACK_START_CLOSE,
                ),
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


def group_target_menu_keyboard(target_user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👍 good",
                    callback_data=f"menu:good:{target_user_id}",
                ),
                InlineKeyboardButton(
                    text="👎 bad",
                    callback_data=f"menu:bad:{target_user_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="👤 Profile",
                    callback_data=f"menu:profile:{target_user_id}",
                ),
                InlineKeyboardButton(
                    text="🚨 Report",
                    callback_data=f"menu:report:{target_user_id}",
                ),
            ],
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
