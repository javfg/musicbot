from __future__ import annotations

from telegram.ext import Application, CallbackContext, ExtBot

from musicbot.config import Config
from musicbot.db.store import Store, StoreRegistry
from musicbot.model.provider import ProviderRegistry


class MusicbotContext(CallbackContext[ExtBot, dict, dict, dict]):
    def __init__(
        self,
        application: Application,
        chat_id: int | None = None,
        user_id: int | None = None,
    ) -> None:
        super().__init__(application=application, chat_id=chat_id, user_id=user_id)
        self.config: Config = application.bot_data['config']
        self.chat_id = chat_id

    @property
    def provider_registry(self) -> ProviderRegistry:
        return self.application.bot_data['provider_registry']

    @property
    def store_registry(self) -> StoreRegistry:
        return self.application.bot_data['store_registry']

    async def get_store(self, chat_id: int | None = None) -> Store:
        chat_id = chat_id or self.chat_id
        if chat_id is None:
            raise ValueError('chat_id is required to get the store')
        return await self.store_registry.get(chat_id)
