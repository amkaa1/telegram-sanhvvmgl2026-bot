from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import SessionLocal
from filters.admin_filter import AdminFilter
from keyboards.admin_menu import admin_menu

router = Router()
router.message.filter(AdminFilter())


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    await message.answer(
        "🔐 <b>Админ цэс</b>\n\n"
        "Доорх товчуудаас сонгож болно.",
        reply_markup=admin_menu(),
    )


@router.message(Command("checkuser"))
async def cmd_checkuser(message: Message) -> None:
    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.answer("Хэрэглэгчийг шалгахын тулд тухайн мессеж дээр reply хийж /checkuser бичнэ үү.")
        return
    target = message.reply_to_message.from_user
    from database.queries import get_or_create_user, get_warning_count

    async with SessionLocal() as session:  # type: AsyncSession
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
