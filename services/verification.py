from __future__ import annotations


def is_verified(user) -> bool:
    return bool(user.is_verified_manual or user.is_verified_auto)


def set_manual_verified(user, value: bool) -> None:
    user.is_verified_manual = value
