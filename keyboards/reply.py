from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

REPLY_BTN_PROFILE = "👤 Profile"
REPLY_BTN_REPORT = "🚨 Report"
REPLY_BTN_GOOD = "🔥 good"
REPLY_BTN_BAD = "❌ bad"

MAIN_MENU_BUTTON_TEXTS = frozenset(
    {REPLY_BTN_PROFILE, REPLY_BTN_REPORT, REPLY_BTN_GOOD, REPLY_BTN_BAD}
)


def main_menu_keyboard(*, selective: bool = False) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=REPLY_BTN_PROFILE),
                KeyboardButton(text=REPLY_BTN_REPORT),
            ],
            [
                KeyboardButton(text=REPLY_BTN_GOOD),
                KeyboardButton(text=REPLY_BTN_BAD),
            ],
        ],
        resize_keyboard=True,
        selective=selective,
    )
