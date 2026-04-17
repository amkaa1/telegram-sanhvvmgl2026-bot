from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.types import ChatMemberUpdated

from config import settings
from database.db import session_scope
from database.models import User
from services.anti_fake import is_suspicious_account
from services.anti_raid import RaidDetector
from services.invite_tracker import process_real_join
from services.reward_messages import format_reward_group_announcement
from services.rewards import check_reward_flags
from services.username_sync import sync_user

router = Router()
raid_detector = RaidDetector()

REWARD_AMOUNT_BY_THRESHOLD: dict[int, int] = {
    500: 75_000,
    1000: 150_000,
    2000: 300_000,
    5000: 700_000,
}


@router.chat_member(F.chat.id == settings.group_id)
async def on_chat_member(update: ChatMemberUpdated) -> None:
    status = update.new_chat_member.status
    if status not in {"member", "administrator"}:
        return
    member = update.new_chat_member.user
    if member is None or member.is_bot:
        return

    async with session_scope() as session:
        joined = await sync_user(session, member)
        was_counted = await process_real_join(session, joined)
        joined.is_suspicious = joined.is_suspicious or is_suspicious_account(
            joined.username, joined.first_name
        )
        if was_counted and joined.referred_by_user_id:
            inviter = await session.get(User, joined.referred_by_user_id)
            if inviter:
                hits = check_reward_flags(inviter)
                try:
                    await update.bot.send_message(
                        inviter.telegram_id,
                        "🎉 <b>Таны invite-аар шинэ хэрэглэгч группд нэгдлээ.</b>\n\n"
                        f"📨 Таны нийт урилга: <b>{inviter.invites_count}</b>",
                        parse_mode=ParseMode.HTML,
                    )
                except Exception:
                    pass
                for level, _legacy_amount in hits:
                    amount_mnt = REWARD_AMOUNT_BY_THRESHOLD.get(level)
                    if amount_mnt is None:
                        continue
                    announce = format_reward_group_announcement(
                        inviter, inviter.invites_count, amount_mnt
                    )
                    try:
                        await update.bot.send_message(
                            settings.group_id,
                            announce,
                            parse_mode=ParseMode.HTML,
                        )
                    except Exception:
                        pass
                    for admin_id in settings.admin_ids:
                        try:
                            await update.bot.send_message(
                                admin_id,
                                announce,
                                parse_mode=ParseMode.HTML,
                            )
                        except Exception:
                            pass
        if raid_detector.record_join():
            joined.is_suspicious = True
            for admin_id in settings.admin_ids:
                try:
                    await update.bot.send_message(
                        admin_id,
                        "Анхаар: anti-raid систем олон шинэ join илрүүллээ. Шинэ аккаунтуудыг шалгана уу.",
                    )
                except Exception:
                    pass
