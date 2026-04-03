def user_label(username: str | None, full_name: str, telegram_id: int) -> str:
    if username:
        return f"@{username}"
    if full_name.strip():
        return full_name
    return str(telegram_id)


def verified_label(is_manual: bool, is_auto: bool) -> str:
    return "Тийм" if (is_manual or is_auto) else "Үгүй"
