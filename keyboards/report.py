from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def report_reason_keyboard(target_user_id: int | None = None) -> InlineKeyboardMarkup:
    prefix = (
        f"report:reason:{target_user_id}:"
        if target_user_id is not None
        else "report_reason:"
    )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Scam", callback_data=f"{prefix}scam")],
            [InlineKeyboardButton(text="Spam", callback_data=f"{prefix}spam")],
            [InlineKeyboardButton(text="Fake", callback_data=f"{prefix}fake")],
            [InlineKeyboardButton(text="Abuse", callback_data=f"{prefix}abuse")],
            [InlineKeyboardButton(text="Other", callback_data=f"{prefix}other")],
        ]
    )


def report_evidence_skip_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Алгасах", callback_data="report_evidence:skip")]
        ]
    )


def admin_report_review_keyboard(report_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Approve Report",
                    callback_data=f"report_review:{report_id}:approve",
                ),
                InlineKeyboardButton(
                    text="Reject Report",
                    callback_data=f"report_review:{report_id}:reject",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Warn User",
                    callback_data=f"report_review:{report_id}:warn",
                ),
                InlineKeyboardButton(
                    text="Mute 1d",
                    callback_data=f"report_review:{report_id}:mute1d",
                ),
                InlineKeyboardButton(
                    text="Ban",
                    callback_data=f"report_review:{report_id}:ban",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Verify",
                    callback_data=f"report_review:{report_id}:verify",
                ),
                InlineKeyboardButton(
                    text="Unverify",
                    callback_data=f"report_review:{report_id}:unverify",
                ),
            ],
        ]
    )


def rating_undo_keyboard(token: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Undo (10 sec)", callback_data=f"rating_undo:{token}")]
        ]
    )
