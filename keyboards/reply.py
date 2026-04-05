from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

REPLY_BTN_PROFILE = "👤 Профайл"
REPLY_BTN_INVITE = "🔗 Урилга"
REPLY_BTN_GOOD = "👍 Дэмжих"
REPLY_BTN_BAD = "👎 Сэрэмжлүүлэх"

MAIN_MENU_BUTTON_TEXTS = frozenset(
    {REPLY_BTN_PROFILE, REPLY_BTN_INVITE, REPLY_BTN_GOOD, REPLY_BTN_BAD}
)


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=REPLY_BTN_PROFILE),
                KeyboardButton(text=REPLY_BTN_INVITE),
            ],
            [
                KeyboardButton(text=REPLY_BTN_GOOD),
                KeyboardButton(text=REPLY_BTN_BAD),
            ],
        ],
        resize_keyboard=True,
    )
