def chunk_telegram_html(text: str, limit: int = 4000) -> list[str]:
    """Split long HTML so each part stays under Telegram's ~4096 char limit."""
    text = text.rstrip()
    if not text:
        return []
    if len(text) <= limit:
        return [text]
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for line in text.split("\n"):
        add_len = len(line) + (1 if current else 0)
        if current_len + add_len > limit and current:
            chunks.append("\n".join(current))
            current = [line]
            current_len = len(line)
        else:
            current_len += add_len
            current.append(line)
    if current:
        chunks.append("\n".join(current))
    out: list[str] = []
    for c in chunks:
        if len(c) <= limit:
            out.append(c)
            continue
        for i in range(0, len(c), limit):
            out.append(c[i : i + limit])
    return out


def user_label(username: str | None, full_name: str, telegram_id: int) -> str:
    if username:
        return f"@{username}"
    if full_name.strip():
        return full_name
    return str(telegram_id)


def verified_label(is_manual: bool, is_auto: bool) -> str:
    return "Тийм" if (is_manual or is_auto) else "Үгүй"
