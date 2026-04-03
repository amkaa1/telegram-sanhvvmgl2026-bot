from aiogram import F, Router
from aiogram.types import CallbackQuery

from config import settings
from database.db import session_scope
from database.queries import get_user_by_telegram_id
from services.reports import submit_report
from services.username_sync import sync_user

router = Router()
PENDING_REPORTS: dict[int, int] = {}


@router.callback_query(F.data.startswith("report:"))
async def cb_report_reason(callback: CallbackQuery) -> None:
    if callback.from_user is None:
        return
    target_id = PENDING_REPORTS.get(callback.from_user.id)
    if target_id is None:
        await callback.answer("Report зорилтот хэрэглэгч олдсонгүй.", show_alert=True)
        return
    reason = callback.data.split(":", maxsplit=1)[1]
    async with session_scope() as session:
        reporter = await sync_user(session, callback.from_user)
        target = await get_user_by_telegram_id(session, target_id)
        if target is None:
            await callback.answer("Хэрэглэгч олдсонгүй.", show_alert=True)
            return
        await submit_report(session, reporter, target, reason)
    PENDING_REPORTS.pop(callback.from_user.id, None)
    await callback.message.answer("Report амжилттай бүртгэгдлээ.")
    for admin_id in settings.admin_ids:
        try:
            await callback.bot.send_message(admin_id, f"Шинэ report: {reason}, target={target_id}")
        except Exception:
            pass
    await callback.answer()
