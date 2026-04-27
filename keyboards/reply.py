from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

REPLY_BTN_PROFILE = "👤 Profile"
                                                                                                                                                                                                                                                                                        REPLY_BTN_REPORT = "⚠️ Report"
REPLY_BTN_GOOD = "👍 Good"
REPLY_BTN_BAD = "👎 Bad"
REPLY_BTN_MENU = "📋 Menu"

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


def group_menu_keyboard() -> ReplyKeyboardMarkup:
    common_kwargs = {
        "keyboard": [[KeyboardButton(text=REPLY_BTN_MENU)]],
        "resize_keyboard": True,
        "input_field_placeholder": "Хүний пост дээр reply хийгээд Menu дарна уу...",
    }
    try:
        return ReplyKeyboardMarkup(is_persistent=True, **common_kwargs)
    except TypeError:
        return ReplyKeyboardMarkup(**common_kwargs)
