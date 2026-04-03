from aiogram import F, Router
from aiogram.types import ChatMemberUpdated

from config import settings
from database.db import session_scope
from services.anti_fake import is_suspicious_account
from services.anti_raid import RaidDetector
from services.invite_tracker import process_real_join
from services.rewards import check_reward_flags
from services.username_sync import sync_user
from utils.debug_log import debug_log

router = Router()
raid_detector = RaidDetector()


@router.chat_member(F.chat.id == settings.group_id)
async def on_chat_member(update: ChatMemberUpdated) -> None:
    status = update.new_chat_member.status
    if status not in {"member", "administrator"}:
        return
    if update.from_user is None:
        return
    async with session_scope() as session:
        joined = await sync_user(session, update.new_chat_member.user)
        was_counted = await process_real_join(session, joined)
        # region agent log
        debug_log("run1", "H4", "handlers/join_events.py:27", "join_processed", {"joined_user_id": joined.telegram_id, "referred_by_db_id": joined.referred_by_user_id or 0, "invite_counted": was_counted})
        # endregion
        joined.is_suspicious = joined.is_suspicious or is_suspicious_account(joined.username, joined.first_name)
        hits = []
        if was_counted and joined.referred_by_user_id:
            inviter = await session.get(type(joined), joined.referred_by_user_id)
            if inviter:
                hits = check_reward_flags(inviter)
                # region agent log
                debug_log("run1", "H5", "handlers/join_events.py:35", "reward_check", {"inviter_id": inviter.telegram_id, "inviter_invite_count": inviter.invite_count, "hits": len(hits)})
                # endregion
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
        for level, amount in hits:
            for admin_id in settings.admin_ids:
                try:
                    await update.bot.send_message(admin_id, f"Шагналын босго хүрлээ: {level} invite -> {amount}")
                except Exception:
                    pass
