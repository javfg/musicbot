from loguru import logger
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, LinkPreviewOptions, Update
from telegram.constants import ParseMode

from musicbot.context import MusicbotContext
from musicbot.db.operations import save_scrobble
from musicbot.model.scrobble import Scrobble, ScrobbleType
from musicbot.security import secured


@secured
async def handle_scrobble(update: Update, context: MusicbotContext) -> None:
    if update.message is None or update.message.text is None or update.message.from_user is None:
        return
    chat_id = update.message.chat_id
    logger.debug(f'creating scrobble for {update.message.from_user.name}...')

    # parse scrobble info from message text
    provider_name, scrobble_type, provider_id = update.message.text.replace('🎧 ', '').split(':')
    logger.debug(f'scrobble provider: {provider_name}, type: {scrobble_type}, id: {provider_id}')

    # create a new scrobble with the parsed info and send a message with it
    new_scrobble = Scrobble(
        id=None,
        dj=update.message.from_user.name,
        dj_id=update.message.from_user.id,
        chat_id=chat_id,
        message_id=None,
        message_content=update.message.text,
        scrobble_type=ScrobbleType(update.message.text.split(':')[1]),
    )
    new_scrobble_message = await context.bot.send_message(
        chat_id=chat_id,
        text=new_scrobble.render(),
    )
    new_scrobble.message_id = new_scrobble_message.message_id

    # iterate through all providers and fill content
    for provider in context.provider_registry.get_all(provider_name):
        old_render = new_scrobble.render()
        try:
            logger.debug(f'filling content from {provider.name}...')
            # fill using provider_id if the provider matches, otherwise try to fill without it
            new_scrobble = await provider.fill(
                scrobble=new_scrobble,
                provider_id=provider_id if provider.name == provider_name else None,
            )
        except Exception as e:
            logger.exception(f'error filling content for {new_scrobble.id} from {provider.name}: {e}')
        new_render = new_scrobble.render()
        if old_render != new_render:
            preferred_preview = None
            for pp in context.config.preferred_previews:
                preferred_preview = new_scrobble.links.get(pp)
                if preferred_preview:
                    break
            await new_scrobble_message.edit_text(
                new_render,
                parse_mode=ParseMode.MARKDOWN_V2,
                link_preview_options=LinkPreviewOptions(
                    url=preferred_preview,
                    prefer_large_media=True,
                    show_above_text=True,
                ),
            )
    logger.debug(f'all providers filled for scrobble {new_scrobble.id}')

    # save the scrobble to the database
    store = await context.get_store()
    async with store.transaction() as conn:
        scrobble_id = await save_scrobble(conn, new_scrobble)
        new_scrobble.id = scrobble_id
        logger.info(f'scrobble saved successfully with id: {scrobble_id}')

    # add the updoot button
    await new_scrobble_message.edit_reply_markup(
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    f'🤌 {new_scrobble.updoots}',
                    callback_data=f'updoot:{new_scrobble.id}',
                ),
            ]
        ]),
        read_timeout=context.config.provider_timeout,
        write_timeout=context.config.provider_timeout,
        pool_timeout=context.config.provider_timeout,
    )
    logger.debug(f'updoot button added to scrobble {new_scrobble.id}')

    # delete the original request message to keep the chat clean
    await update.message.delete()
    logger.debug(f'original message deleted for scrobble {new_scrobble.id}')
