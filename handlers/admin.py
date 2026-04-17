from html import escape

from aiogram import F
from aiogram.filters import Command
from aiogram import Router
from aiogram.types import CallbackQuery, Message
from analytics.stats import build_stats_text
from config import settings
from database.db import SessionLocal
from utils.logger import logger
from database.queries import get_top_users_by_invites, get_top_users_by_reputation
from filters.admin_filter import AdminFilter
from keyboards.admin_menu import admin_menu
from utils.text import chunk_telegram_html

router = Router()
router.message.filter(AdminFilter())


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    await message.answer(
        "🔐 <b>Админ цэс</b>\n\n"
        "Доорх товчуудаас сонгож болно.",
        reply_markup=admin_menu(),
    )
@router.callback_query(F.data.in_({"admin_stats", "admin_leaderboard"}))
async def admin_menu_callback(call: CallbackQuery) -> None:
    if call.from_user is None or call.from_user.id not in settings.admin_ids:
        await call.answer("Энэ цэс зөвхөн админд зориулагдсан.", show_alert=True)
        return

    await call.answer()
    if call.message is None:
        return
    chat_id = call.message.chat.id

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
        for part in parts:
            await call.bot.send_message(chat_id, part)
    except Exception as exc:
        logger.exception("admin_menu_callback error: %s", exc)
        await call.bot.send_message(
            chat_id,
            "⚠️ Админ цэсний үйлдэл ажиллахгүй байна. Дахин оролдоно уу эсвэл /stats ашиглана уу.",
        )


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
