import time
from functools import wraps

import telegram
from loguru import logger
from telegram.constants import ChatMemberStatus

from musicbot.config import Config
from musicbot.context import MusicbotContext

membership_cache: dict[int, tuple[bool, float]] = {}


async def is_user_allowed(bot: telegram.Bot, user_id: int, config: Config) -> bool:
    now = time.time()
    if user_id in membership_cache:
        result, ts = membership_cache[user_id]
        if now - ts < config.allowlist_cache_ttl:
            logger.trace(f'cache hit for user {user_id} (allowed: {result})')
            return result

    allowed = False
    for chat_id in config.chat_id_whitelist:
        try:
            logger.trace(f'checking membership for user {user_id} in chat {chat_id}...')
            member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            if member.status in [
                ChatMemberStatus.ADMINISTRATOR,
                ChatMemberStatus.OWNER,
                ChatMemberStatus.MEMBER,
            ]:
                logger.trace(f'user {user_id} is a member of chat {chat_id} (status: {member.status})')
                allowed = True
                break
        except Exception:
            logger.error(f'failed to check membership for user {user_id} in chat {chat_id}', exc_info=True)
            continue

    membership_cache[user_id] = (allowed, now)
    return allowed


def is_chat_allowed(chat_id: int, chat_id_whitelist: list[int]) -> bool:
    logger.trace(f'checking if chat {chat_id} is allowed in {chat_id_whitelist}...')
    return chat_id in chat_id_whitelist


def secured(handler):
    @wraps(handler)
    async def wrapper(update: telegram.Update, context: MusicbotContext):
        if update.effective_user is None or update.effective_user.id is None:
            logger.warning('received update with no effective user, skipping')
            return

        user_id = update.effective_user.id

        if update.effective_chat is not None:
            if not is_chat_allowed(update.effective_chat.id, context.config.chat_id_whitelist):
                logger.warning(f'received update from disallowed chat {update.effective_chat.id}, skipping')
                return

        if not await is_user_allowed(context.bot, user_id, context.config):
            logger.warning(f'received update from disallowed user {user_id}, skipping')
            return

        return await handler(update, context)

    return wrapper
