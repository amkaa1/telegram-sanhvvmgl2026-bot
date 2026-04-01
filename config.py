import os
from dataclasses import dataclass
from typing import List

from dotenv import load_dotenv


load_dotenv()


def _get_env(name: str, default: str | None = None, required: bool = True) -> str:
    value = os.getenv(name, default)
    if required and (value is None or value.strip() == ""):
        raise RuntimeError(f"Environment variable {name} is required but not set.")
    return value  # type: ignore[return-value]


def _parse_admin_ids(raw: str | None) -> List[int]:
    if not raw:
        return []
    result: List[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            result.append(int(part))
        except ValueError:
            continue
    return result


@dataclass(frozen=True)
class Settings:
    bot_token: str
    database_url: str
    group_id: int
    admin_ids: List[int]


def load_settings() -> Settings:
    bot_token = _get_env("BOT_TOKEN")
    database_url = _get_env("DATABASE_URL")
    group_id = int(_get_env("GROUP_ID"))
    admin_ids = _parse_admin_ids(os.getenv("ADMIN_IDS"))
    return Settings(
        bot_token=bot_token,
        database_url=database_url,
        group_id=group_id,
        admin_ids=admin_ids,
    )


settings = load_settings()

