from __future__ import annotations


def is_suspicious_account(username: str | None, first_name: str | None) -> bool:
    if not username:
        return True
    if not first_name:
        return True
    if len(username) < 4:
        return True
    return False
