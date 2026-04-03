from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

import json
import time
import urllib.request
from urllib.error import URLError

from database.db import SessionLocal
from database.queries import get_or_create_user
from services.reputation import get_trust_level, is_verified


router = Router()

HTTP_INGEST_URL = (
    "http://127.0.0.1:7779/ingest/606d69a6-5591-40cf-90e4-cd0a812fc949"
)
DEBUG_SESSION_ID = "20ebd7"


def _emit_debuglog_http(
    *,
    run_id: str,
    hypothesis_id: str,
    location: str,
    message: str,
    data: dict,
) -> None:
    """Emit NDJSON log via local debug ingest endpoint."""
    payload = {
        "sessionId": DEBUG_SESSION_ID,
        "runId": run_id,
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    try:
        req = urllib.request.Request(
            HTTP_INGEST_URL,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "X-Debug-Session-Id": DEBUG_SESSION_ID,
            },
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        )
        with urllib.request.urlopen(req, timeout=1.5) as _resp:
            pass
    except (URLError, TimeoutError, OSError):
        return


@router.message(Command("profile"))
async def cmd_profile(message: Message) -> None:
    if message.from_user is None:
        return

    _emit_debuglog_http(
        run_id="pre-fix",
        hypothesis_id="P0_profile_cmd_received",
        location="handlers/profile.py:cmd_profile",
        message="cmd_profile received",
        data={
            "has_text": bool(message.text),
            "has_reply": bool(message.reply_to_message),
        },
    )
    print(
        "DEBUG_PROFILE_CMD",
        f"has_text={bool(message.text)}",
        f"has_reply={bool(message.reply_to_message)}",
    )

    # 1) Reply takes priority
    if message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user
        print("DEBUG_PROFILE_TARGET_VIA", "reply")
        _emit_debuglog_http(
            run_id="pre-fix",
            hypothesis_id="P1_reply_priority",
            location="handlers/profile.py:cmd_profile",
            message="Target resolved from reply",
            data={
                "resolved_via": "reply",
            },
        )
    else:
        # 2) Parse command args: /profile @username
        arg_username: str | None = None
        text = (message.text or "").strip()
        if text:
            # Accept both "/profile @username" and "/profile@username".
            if text.startswith("/profile@"):
                candidate = text.split("/profile@", 1)[1].strip()
                token = candidate.split(maxsplit=1)[0].strip()
                if token:
                    arg_username = token.lstrip("@").strip()
            else:
                parts = text.split(maxsplit=1)
                if len(parts) == 2:
                    raw = parts[1].strip()
                    token = raw.split(maxsplit=1)[0]
                    if token.startswith("@") and len(token) > 1:
                        arg_username = token[1:].strip()
        print("DEBUG_PROFILE_USERNAME_ARG_PRESENT", f"{bool(arg_username)}")

        # 3) Fallback to sender, unless @username resolves
        target = message.from_user
        resolved_via_source = "sender"
        if arg_username:
            try:
                resolved = await message.bot.get_chat(f"@{arg_username}")
                # aiogram may return Chat-like object; normalize fields we need.
                resolved_id = getattr(resolved, "id", None)
                if resolved_id is not None:
                    target = resolved
                    resolved_via_source = "username"
                    print("DEBUG_PROFILE_RESOLVE_USERNAME", "success")
                    _emit_debuglog_http(
                        run_id="pre-fix",
                        hypothesis_id="P2_username_resolve_success",
                        location="handlers/profile.py:cmd_profile",
                        message="Target resolved from @username",
                        data={
                            "resolved_via": "username",
                            "username_arg_present": True,
                        },
                    )
            except Exception:  # noqa: BLE001
                # If username can't be resolved, show sender's profile.
                target = message.from_user
                print("DEBUG_PROFILE_RESOLVE_USERNAME", "failed")
                _emit_debuglog_http(
                    run_id="pre-fix",
                    hypothesis_id="P3_username_resolve_failed",
                    location="handlers/profile.py:cmd_profile",
                    message="Username resolve failed; fallback to sender",
                    data={"resolved_via": "sender", "username_arg_present": True},
                )
        print("DEBUG_PROFILE_TARGET_VIA", resolved_via_source)
        _emit_debuglog_http(
            run_id="pre-fix",
            hypothesis_id="P4_target_fallback_decision",
            location="handlers/profile.py:cmd_profile",
            message="Target finalized (non-reply path)",
            data={
                "resolved_via": resolved_via_source,
            },
        )

    # Normalize display name for both User and Chat-like objects.
    target_full_name = (
        getattr(target, "full_name", None)
        or " ".join(
            [
                getattr(target, "first_name", "") or "",
                getattr(target, "last_name", "") or "",
            ]
        ).strip()
        or getattr(target, "title", None)
        or str(getattr(target, "username", "") or message.from_user.id)
    )
    target_id = int(getattr(target, "id", message.from_user.id))
    target_username = getattr(target, "username", None)
    target_first_name = getattr(target, "first_name", "") or ""
    target_last_name = getattr(target, "last_name", "") or ""

    async with SessionLocal() as session:  # type: AsyncSession
        user = await get_or_create_user(
            session,
            telegram_id=target_id,
            username=target_username,
            first_name=target_first_name,
            last_name=target_last_name,
        )

    _emit_debuglog_http(
        run_id="pre-fix",
        hypothesis_id="P5_db_user_created_or_fetched",
        location="handlers/profile.py:cmd_profile",
        message="DB lookup complete (profile rendering)",
        data={
            "has_target_username": bool(target_username),
            "has_target_name": bool(target_full_name),
        },
    )
    print(
        "DEBUG_PROFILE_DB_DONE",
        f"has_target_username={bool(target_username)}",
        f"has_target_name={bool(target_full_name)}",
    )

    level = get_trust_level(user.reputation_positive)
    verified_badge = "✔ Verified" if is_verified(user.reputation_positive) or user.verified else ""

    lines: list[str] = []
    lines.append(f"👤 Профайл: <a href=\"tg://user?id={target_id}\">{target_full_name}</a>")
    if target_username:
        lines.append(f"🔗 Username: @{target_username}")
    lines.append("")
    lines.append(f"✅ Trust Level: <b>{level}</b>")
    lines.append(f"👍 Сайн: <b>{user.reputation_positive}</b>")
    lines.append(f"👎 Муу: <b>{user.reputation_negative}</b>")
    lines.append(f"📨 Урилга: <b>{user.invites_count}</b>")
    if verified_badge:
        lines.append(f"🔒 Статус: <b>{verified_badge}</b>")

    await message.answer("\n".join(lines))

