from aiogram.filters import BaseFilter
from aiogram.types import Message

from config import settings


class AdminFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user and message.from_user.id in settings.admin_ids

