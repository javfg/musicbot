from datetime import datetime

from loguru import logger
from telegram import Update

from musicbot.context import MusicbotContext
from musicbot.db.operations import get_ranking, get_user_stats
from musicbot.security import secured
from musicbot.util import _, get_timeframe


@secured
async def handle_stats(update: Update, context: MusicbotContext):
    logger.info(f'received stats command: {update}')
    if update.message is None or update.message.from_user is None:
        return

    dj_username = update.message.from_user.username
    dj_id = update.message.from_user.id
    chat_id = update.message.chat_id

    logger.info(f'handling stats command from user {dj_username} ({dj_id}) in chat {chat_id}')

    store = await context.get_store()
    async with store.transaction() as conn:
        user_stats = await get_user_stats(conn, dj_id, chat_id)

    message = f'*📈 Stats for DJ @{dj_username}:*\n\n'
    if user_stats.scrobbles == 0:
        message += 'Nothing so far\\.\\.\\. 😞'
    else:
        message += f'*🎧 Submissions:* {user_stats.scrobbles}\n'
        message += '*🏷️ Favorite tags:*'
        for index, tag in enumerate(user_stats.fav_tags):
            message += f'\n        {index + 1}\\. {_(tag[0])} \\({tag[1]!s}\\)'
        message += f'\n*🌈 Different tags:* {user_stats.different_tags!s}'

    await context.bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode='MarkdownV2',
        disable_web_page_preview=True,
    )


async def _handle_ranking(
    context: MusicbotContext,
    chat_id: int,
    after: datetime = datetime.min,
    caption: str = 'All\\-time',
    max_results: int = 10,
):
    store = await context.get_store()
    async with store.transaction() as conn:
        ranking = await get_ranking(
            conn,
            chat_id,
            after=after,
            before=datetime.max,
            max_results=max_results,
        )

    trophies = ['🥇', '🥈', '🥉'] + ['➖'] * max_results  # noqa: RUF001
    message = f'*🏆 {caption} _DJ ranking_*:\n'

    if not ranking:
        message += 'Nothing so far\\.\\.\\. 😞'
    else:
        for index, (dj, scrobble_count) in enumerate(ranking.items()):
            message += f'\n{trophies[index]} {index + 1}\\. {_(dj)}: {_(str(scrobble_count))}'

    await context.bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode='MarkdownV2',
        disable_web_page_preview=True,
    )


@secured
async def handle_ranking(update: Update, context: MusicbotContext):
    logger.info(f'received ranking command: {update}')
    if update.message is None:
        return

    chat_id = update.message.chat_id
    logger.info(f'handling ranking command in chat {chat_id}')

    await _handle_ranking(context, chat_id, after=get_timeframe('month'))


async def handle_monthly_ranking(context: MusicbotContext):
    for chat_id in context.config.chat_id_whitelist:
        await _handle_ranking(
            context,
            chat_id=int(chat_id),
            after=get_timeframe('month'),
            caption='Monthly',
        )
