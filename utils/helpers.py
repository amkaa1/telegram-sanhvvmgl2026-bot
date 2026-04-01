from aiogram.types import User as TgUser


def format_username(user: TgUser) -> str:
    if user.username:
        return f"@{user.username}"
    full_name = " ".join(filter(None, [user.first_name, user.last_name]))
    if full_name.strip():
        return full_name.strip()
    return str(user.id)


def bold(text: str) -> str:
    return f"<b>{text}</b>"

