from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from utils.debug_log import debug_log

load_dotenv()


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        # region agent log
        debug_log("run3", "H1", "config.py:16", "missing_env", {"name": name})
        # endregion
        raise RuntimeError(f"'{name}' орчны хувьсагч заавал тохируулагдсан байх ёстой.")
    return value


def _parse_int(value: str, name: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"'{name}' бүхэл тоо байх ёстой.") from exc


def _parse_admin_ids(raw: str) -> tuple[int, ...]:
    values: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        values.append(_parse_int(part, "ADMIN_IDS"))
    return tuple(values)


def _normalize_database_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql+asyncpg://"):
        return url
    raise RuntimeError("DATABASE_URL нь PostgreSQL холбоос байх ёстой.")


@dataclass(frozen=True)
class Settings:
    bot_token: str
    bot_username: str
    database_url: str
    group_id: int
    admin_ids: tuple[int, ...]
    log_level: str


def load_settings() -> Settings:
    return Settings(
        bot_token=_require_env("BOT_TOKEN"),
        bot_username=_require_env("BOT_USERNAME").lstrip("@"),
        database_url=_normalize_database_url(_require_env("DATABASE_URL")),
        group_id=_parse_int(_require_env("GROUP_ID"), "GROUP_ID"),
        admin_ids=_parse_admin_ids(_require_env("ADMIN_IDS")),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )


settings = load_settings()

