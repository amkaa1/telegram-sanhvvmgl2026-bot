import json
import time
from html import escape
from pathlib import Path
import urllib.request
from urllib.error import URLError

from aiogram import F
from aiogram.filters import Command
from aiogram import Router
from aiogram.types import CallbackQuery, Message
from analytics.stats import build_stats_text
from config import settings
from database.db import SessionLocal
from database.queries import get_top_users_by_invites, get_top_users_by_reputation
from filters.admin_filter import AdminFilter
from keyboards.admin_menu import admin_menu
from utils.text import chunk_telegram_html

router = Router()
router.message.filter(AdminFilter())

LOG_PATH = Path(__file__).resolve().parents[1] / "debug-20ebd7.log"

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
    """Emit NDJSON log to local debug ingest endpoint (not filesystem-bound)."""
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
        # Don't break bot behavior if debug endpoint isn't reachable.
        return


def _callback_reply_chat_id(call: CallbackQuery) -> int | None:
    """Where to send follow-up text after an inline button (message may be missing)."""
    if call.message is not None:
        chat = getattr(call.message, "chat", None)
        if chat is not None and getattr(chat, "id", None) is not None:
            return int(chat.id)
    if call.from_user is not None:
        return int(call.from_user.id)
    return None


# #region agent log
try:
    payload = {
        "sessionId": "20ebd7",
        "runId": "pre-fix",
        "hypothesisId": "H0_module_load_admin_router",
        "location": "handlers/admin.py:module_load",
        "message": "admin handlers module loaded",
        "data": {},
        "timestamp": int(time.time() * 1000),
    }
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
except Exception:  # noqa: BLE001
    # Avoid crashing bot on filesystem/log failures.
    print("DEBUGLOG_WRITE_FAIL: handlers/admin.py:module_load")
_emit_debuglog_http(
    run_id="pre-fix",
    hypothesis_id="H0_module_load_admin_router",
    location="handlers/admin.py:module_load",
    message="admin handlers module loaded (http)",
    data={},
)
# #endregion


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    await message.answer(
        "🔐 <b>Админ цэс</b>\n\n"
        "Доорх товчуудаас сонгож болно.",
        reply_markup=admin_menu(),
    )
    _emit_debuglog_http(
        run_id="pre-fix",
        hypothesis_id="H2_cmd_admin_invoked",
        location="handlers/admin.py:cmd_admin",
        message="Received /admin and sent inline menu (http)",
        data={"chat_id": message.chat.id if message.chat else None},
    )


@router.callback_query(F.data.in_({"admin_stats", "admin_leaderboard"}))
async def admin_menu_callback(call: CallbackQuery) -> None:
    if call.from_user is None or call.from_user.id not in settings.admin_ids:
        await call.answer("Энэ цэс зөвхөн админд зориулагдсан.", show_alert=True)
        return

    print(
        "DEBUG_CB_START",
        f"data={call.data}",
        f"from_user_id={getattr(call.from_user, 'id', None)}",
    )

    # #region agent log
    payload = {
        "sessionId": "20ebd7",
        "runId": "pre-fix",
        "hypothesisId": "H1_admin_menu_missing_callback_handlers",
        "location": "handlers/admin.py:admin_menu_callback",
        "message": "Admin menu callback received",
        "data": {"callback_data": call.data},
        "timestamp": int(time.time() * 1000),
    }
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001
        print("DEBUGLOG_WRITE_FAIL: handlers/admin.py:admin_menu_callback:pre")
    _emit_debuglog_http(
        run_id="pre-fix",
        hypothesis_id="H1_admin_menu_missing_callback_handlers",
        location="handlers/admin.py:admin_menu_callback",
        message="Admin menu callback received (http)",
        data={
            "callback_data": call.data,
            "has_message": call.message is not None,
        },
    )
    # #endregion

    await call.answer()

    chat_id = _callback_reply_chat_id(call)
    print("DEBUG_CB_CHAT_ID", f"data={call.data}", f"chat_id={chat_id}", f"has_message={call.message is not None}")
    _emit_debuglog_http(
        run_id="pre-fix",
        hypothesis_id="H1_admin_menu_missing_callback_handlers",
        location="handlers/admin.py:admin_menu_callback",
        message="Resolved chat_id for callback (http)",
        data={"callback_data": call.data, "chat_id": chat_id},
    )
    if chat_id is None:
        print("DEBUG_CB_ABORT_NO_CHAT")
        _emit_debuglog_http(
            run_id="pre-fix",
            hypothesis_id="H1_admin_menu_missing_callback_handlers",
            location="handlers/admin.py:admin_menu_callback",
            message="Abort: no chat_id for callback (http)",
            data={"callback_data": call.data},
        )
        return

    try:
        async with SessionLocal() as session:
            if call.data == "admin_stats":
                text = await build_stats_text(session)
            else:
                top_rep = await get_top_users_by_reputation(session, limit=10)
                top_inv = await get_top_users_by_invites(session, limit=10)

                rep_lines: list[str] = ["⭐ <b>Итгэлцлээр тэргүүлэгчид</b>"]
                if top_rep:
                    for i, u in enumerate(top_rep, start=1):
                        label = escape(u.username) if u.username else str(u.telegram_id)
                        rep_lines.append(
                            f"{i}. <a href=\"tg://user?id={u.telegram_id}\">{label}</a> "
                            f"- 👍 {u.reputation_positive} / 👎 {u.reputation_negative}"
                        )
                else:
                    rep_lines.append("— Одоогоор өгөгдөл алга.")

                inv_lines: list[str] = ["📨 <b>Урилгаар тэргүүлэгчид</b>"]
                if top_inv:
                    for i, u in enumerate(top_inv, start=1):
                        label = escape(u.username) if u.username else str(u.telegram_id)
                        inv_lines.append(
                            f"{i}. <a href=\"tg://user?id={u.telegram_id}\">{label}</a> "
                            f"- {u.invites_count:,} урилга"
                        )
                else:
                    inv_lines.append("— Одоогоор өгөгдөл алга.")

                text = "🏆 <b>Лидерүүд</b>\n\n" + "\n".join(rep_lines) + "\n\n" + "\n".join(inv_lines)
        parts = chunk_telegram_html(text)
        print("DEBUG_CB_REPLY_PARTS", f"data={call.data}", f"parts={len(parts)}", f"text_len={len(text)}")
        _emit_debuglog_http(
            run_id="pre-fix",
            hypothesis_id="H4_html_chunking_or_empty_reply",
            location="handlers/admin.py:admin_menu_callback",
            message="Prepared reply parts (http)",
            data={
                "callback_data": call.data,
                "parts": len(parts),
                "text_len": len(text),
            },
        )
        for part in parts:
            await call.bot.send_message(chat_id, part)
    except Exception as exc:  # noqa: BLE001
        print("DEBUG_CB_EXCEPTION", f"data={call.data}", f"error={type(exc).__name__}", f"msg={exc}")
        _emit_debuglog_http(
            run_id="pre-fix",
            hypothesis_id="H5_db_or_render_exception",
            location="handlers/admin.py:admin_menu_callback",
            message="Admin menu action failed (http)",
            data={
                "callback_data": call.data,
                "error_type": type(exc).__name__,
                "error": str(exc),
            },
        )
        # #region agent log
        try:
            payload = {
                "sessionId": "20ebd7",
                "runId": "post-fix",
                "hypothesisId": "H1_admin_menu_missing_callback_handlers",
                "location": "handlers/admin.py:admin_menu_callback",
                "message": "Admin menu action failed",
                "data": {"callback_data": call.data, "error_type": type(exc).__name__},
                "timestamp": int(time.time() * 1000),
            }
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=False) + "\n")
        except Exception:  # noqa: BLE001
            pass
        # #endregion
        try:
            await call.bot.send_message(
                chat_id,
                "⚠️ Админ цэсний үйлдэл ажиллахгүй байна. Дахин оролдоно уу эсвэл /stats ашиглана уу.",
            )
        except Exception:  # noqa: BLE001
            pass
        return

    # #region agent log
    try:
        payload = {
            "sessionId": "20ebd7",
            "runId": "post-fix",
            "hypothesisId": "H1_admin_menu_missing_callback_handlers",
            "location": "handlers/admin.py:admin_menu_callback",
            "message": "Admin menu action completed",
            "data": {"callback_data": call.data, "ok": True},
            "timestamp": int(time.time() * 1000),
        }
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001
        pass
    # #endregion


@router.message(Command("checkuser"))
async def cmd_checkuser(message: Message) -> None:
    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.answer("Хэрэглэгчийг шалгахын тулд тухайн мессеж дээр reply хийж /checkuser бичнэ үү.")
        return
    target = message.reply_to_message.from_user
    from database.queries import get_or_create_user, get_warning_count

    async with SessionLocal() as session:
        u = await get_or_create_user(
            session,
            telegram_id=target.id,
            username=target.username,
            first_name=target.first_name,
            last_name=target.last_name,
        )
        warns = await get_warning_count(session, u)
        suspicious = u.is_suspicious
        inv_count = u.invites_count
        await session.commit()
    await message.answer(
        f"ID: <code>{target.id}</code>\n"
        f"Анхааруулга: {warns}\n"
        f"Сэжигтэй: {'Тийм' if suspicious else 'Үгүй'}\n"
        f"Урилга: {inv_count}"
    )
