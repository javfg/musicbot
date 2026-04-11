from loguru import logger

from musicbot.context import MusicbotContext
from musicbot.db.operations import get_scrobble_summaries
from musicbot.model.scrobble import ScrobbleSummary
from musicbot.util import get_timeframe


async def handle_digest(context: MusicbotContext, since: str = 'day') -> None:
    logger.info(f'generating {since}ly digests...')
    for chat_id in context.config.chat_id_whitelist:
        logger.info(f'generating {since}ly digest for chat {chat_id}')
        store = await context.get_store(chat_id)
        async with store.transaction() as conn:
            scrobble_summaries = await get_scrobble_summaries(
                conn,
                chat_id=int(chat_id),
                after=get_timeframe(since),
            )
            if not scrobble_summaries:
                logger.info(f'skipping empty {since}ly digest for chat {chat_id}')
                continue
            message = create_digest_message(scrobble_summaries, since)
            await context.bot.send_message(
                chat_id=int(chat_id),
                text=message,
                parse_mode='MarkdownV2',
                disable_web_page_preview=True,
            )
            logger.info(f'{since}ly digest sent for chat {chat_id}')


async def handle_daily_digest(context: MusicbotContext) -> None:
    await handle_digest(context, since='day')


async def handle_weekly_digest(context: MusicbotContext) -> None:
    await handle_digest(context, since='week')


def create_digest_message(scrobble_summaries: list[ScrobbleSummary], caption: str) -> str:
    if caption in ['month', 'week', 'day']:
        message = f'*📒 Digest for the {caption}:*\n'
    if not len(scrobble_summaries):
        message += 'Nothing so far\\.\\.\\. 😞'
    message += ('\n').join([s.render() for s in scrobble_summaries])

    return message
