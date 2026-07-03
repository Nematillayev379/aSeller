import time
from typing import Callable, Dict, Any
from aiogram import BaseMiddleware
from aiogram.types import Message


class AntiFloodMiddleware(BaseMiddleware):
    def __init__(self, limit: int = 3, period: float = 1.0):
        self.limit = limit
        self.period = period
        self.user_timestamps: Dict[int, list] = {}
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Any],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id if event.from_user else 0

        if user_id not in self.user_timestamps:
            self.user_timestamps[user_id] = []

        now = time.time()
        self.user_timestamps[user_id] = [
            t for t in self.user_timestamps[user_id] if now - t < self.period
        ]

        if len(self.user_timestamps[user_id]) >= self.limit:
            await event.answer("\u23f0 Juda ko'p so'rov. Biroz kuting.")
            return None

        self.user_timestamps[user_id].append(now)
        return await handler(event, data)
