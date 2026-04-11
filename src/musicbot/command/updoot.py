from loguru import logger
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update

from musicbot.context import MusicbotContext
from musicbot.db.operations import updoot_scrobble
from musicbot.security import secured


@secured
async def handle_updoot(update: Update, context: MusicbotContext) -> None:
    query = update.callback_query
    if not query or not query.data or not query.data.startswith('updoot:'):
        return
    user_id = query.from_user.id
    scrobble_id = int(query.data.split(':')[1])

    logger.debug(f'handling updoot for scrobble {scrobble_id} by user {user_id}')

    store = await context.get_store()
    async with store.transaction() as conn:
        updooted, new_count = await updoot_scrobble(
            conn,
            scrobble_id=scrobble_id,
            user_id=query.from_user.id,
        )

        if updooted:
            logger.info(f'user {user_id} updooted scrobble {scrobble_id}, new count: {new_count}')

            await query.answer()
            await query.edit_message_reply_markup(
                InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(f'🤌 {new_count}', callback_data=f'updoot:{scrobble_id}'),
                    ]
                ])
            )
        else:
            logger.info(f'user {user_id} already updooted scrobble {scrobble_id}')
            await query.answer('You have already updooted this scrobble!', show_alert=True)
