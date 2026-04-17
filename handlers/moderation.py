import datetime as dt

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import ChatPermissions, Message
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database.db import SessionLocal
from database.queries import add_warning, get_or_create_user, get_warning_count, set_mute


router = Router()


def _is_admin(message: Message) -> bool:
    return message.from_user is not None and message.from_user.id in settings.admin_ids


@router.message(Command("warn"))
async def cmd_warn(message: Message) -> None:
    if not _is_admin(message):
        return
    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.answer("⚠️ Анхааруулга өгөхийн тулд тухайн мессеж дээр reply хийж /warn гэж бичнэ үү.")
        return

    target = message.reply_to_message.from_user
    reason = (
        message.text.split(maxsplit=1)[1].strip()
        if message.text and len(message.text.split(maxsplit=1)) == 2
        else None
    )

    async with SessionLocal() as session:  # type: AsyncSession
        user = await get_or_create_user(
            session,
            telegram_id=target.id,
            username=target.username,
            first_name=target.first_name,
            last_name=target.last_name,
        )
        await add_warning(session, user, reason)
        count = await get_warning_count(session, user)

        if count >= 3:
            until = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc) + dt.timedelta(
                hours=24
            )
            await set_mute(session, user, until)
            await session.commit()
            await message.chat.restrict(
                user_id=target.id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=until,
            )
            await message.answer(
                f"⛔ @{target.username or target.id} 3 анхааруулга авсан тул 24 цагийн турш чимээгүй боллоо."
            )
        else:
            await session.commit()
            await message.answer(
                f"⚠️ @{target.username or target.id} анхааруулга авлаа. Нийт анхааруулга: {count}."
            )


@router.message(Command("mute"))
async def cmd_mute(message: Message) -> None:
    if not _is_admin(message):
        return
    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.answer("⏸ Чимээгүй болгохын тулд тухайн мессеж дээр reply хийж /mute гэж бичнэ үү.")
        return

    target = message.reply_to_message.from_user
    async with SessionLocal() as session:  # type: AsyncSession
        user = await get_or_create_user(
            session,
            telegram_id=target.id,
            username=target.username,
            first_name=target.first_name,
            last_name=target.last_name,
        )
        until = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc) + dt.timedelta(
            hours=24
        )
        await set_mute(session, user, until)
        await session.commit()

    try:
        await message.chat.restrict(
            user_id=target.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until,
        )
        await message.answer(
            f"⏸ @{target.username or target.id} 24 цагийн турш чимээгүй боллоо."
        )
    except Exception:
        await message.answer("⚠️ Bot-д эрх хүрэлцэхгүй тул mute хийж чадсангүй ⚠️")


@router.message(Command("unban"))
async def cmd_unban(message: Message) -> None:
    if not _is_admin(message):
        return
    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.answer("✅ Ban-ийг цуцлахын тулд тухайн мессеж дээр reply хийж /unban гэж бичнэ үү.")
        return

    target = message.reply_to_message.from_user
    try:
        await message.chat.unban(user_id=target.id, only_if_banned=True)
        await message.answer(f"✅ @{target.username or target.id} ban-ээс чөлөөлөгдлөө.")
    except Exception:
        await message.answer("⚠️ Bot-д эрх хүрэлцэхгүй тул unban хийж чадсангүй ⚠️")


@router.message(Command("ban"))
async def cmd_ban(message: Message) -> None:
    if not _is_admin(message):
        return
    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.answer("⛔ Ban хийхийн тулд тухайн мессеж дээр reply хийж /ban гэж бичнэ үү.")
        return

    target = message.reply_to_message.from_user
    try:
        await message.chat.ban(user_id=target.id)
        await message.answer(f"⛔ @{target.username or target.id} группээс бан хийгдлээ.")
    except Exception:
        await message.answer("⚠️ Bot-д эрх хүрэлцэхгүй тул ban хийж чадсангүй ⚠️")


@router.message(Command("verify"))
async def cmd_verify(message: Message) -> None:
    if not _is_admin(message):
        return
    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.answer("✅ Verify хийх хэрэглэгч дээр reply хийгээд /verify гэж бичнэ үү.")
        return
    target = message.reply_to_message.from_user
    async with SessionLocal() as session:
        user = await get_or_create_user(
            session,
            telegram_id=target.id,
            username=target.username,
            first_name=target.first_name,
            last_name=target.last_name,
        )
        user.manual_badge_override = "Verified"
        user.verified = True
        await session.commit()
    await message.answer(f"✅ @{target.username or target.id} хэрэглэгчийг verify болголоо.")


@router.message(Command("unverify"))
async def cmd_unverify(message: Message) -> None:
    if not _is_admin(message):
        return
    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.answer("✅ Unverify хийх хэрэглэгч дээр reply хийгээд /unverify гэж бичнэ үү.")
        return
    target = message.reply_to_message.from_user
    async with SessionLocal() as session:
        user = await get_or_create_user(
            session,
            telegram_id=target.id,
            username=target.username,
            first_name=target.first_name,
            last_name=target.last_name,
        )
        user.manual_badge_override = None
        user.verified = False
        await session.commit()
    await message.answer(f"✅ @{target.username or target.id} хэрэглэгчийн verify-г цуцаллаа.")

