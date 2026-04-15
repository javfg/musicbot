import re

from loguru import logger
from telegram import LinkPreviewOptions, Update
from telegram.constants import ParseMode
from telegram.ext import filters

from musicbot.context import MusicbotContext
from musicbot.db.operations import check_amend_request, update_scrobble_links
from musicbot.model.provider import Amender
from musicbot.security import secured


class ReplyToBotFilter(filters.BaseFilter):
    def __init__(self, bot_id: int):
        self.bot_id = bot_id
        super().__init__()

    def check_update(self, update: Update) -> bool:
        if update.message is None:
            return False

        message = update.message
        if not message.text or not message.entities:
            return False

        urls = [e for e in message.entities if e.type in ('url', 'text_link')]
        if not urls or len(urls) != 1 or urls[0].offset != 0 or urls[0].length != len(message.text):
            return False

        if (
            message.reply_to_message is None
            or message.reply_to_message.from_user is None
            or message.reply_to_message.from_user.id != self.bot_id
        ):
            return False

        logger.debug(f'message {message.message_id} is a valid amend request')
        return True


@secured
async def handle_amend(update: Update, context: MusicbotContext) -> None:
    if (
        update.effective_chat is None
        or update.message is None
        or update.message.text is None
        or update.message.from_user is None
        or update.message.reply_to_message is None
        or update.message.reply_to_message.text is None
        or update.message.reply_to_message.from_user is None
    ):
        return

    scrobble_message = update.message.reply_to_message
    amender_user_id = update.message.from_user.id
    new_link = update.message.text
    logger.debug(f'user {amender_user_id} request amend {scrobble_message.message_id} with new link: {new_link}')

    # first check if the amend request is valid
    store = await context.get_store()
    async with store.transaction() as conn:
        try:
            await check_amend_request(conn, scrobble_message.message_id, amender_user_id)
        except PermissionError:
            chat_id = update.message.chat_id
            message_id = scrobble_message.message_id
            link = f'https://t.me/c/{str(chat_id)[4:]}/{message_id}'
            await context.bot.send_message(
                amender_user_id,
                f'Regarding:\n\n{link}\n\nOnly the original submitter can amend the scrobble links.',
            )
            await update.message.delete()
            return

    # then find the correct amendment for the given reply
    correct_amender: Amender | None = None
    for amender in context.provider_registry.amenders:
        if re.match(amender.pattern, new_link):
            correct_amender = amender
            break

    # if no amender was found, reply with an error message and return
    if correct_amender is None:
        logger.warning(f'no amender found for message {update.message.message_id} with text "{new_link}"')
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='I do not know what to do with that.',
            reply_to_message_id=update.message.message_id,
        )
        return
    logger.debug(f'found amender {correct_amender.name} for message {update.message.message_id} with text "{new_link}"')

    # update the scrobble in the db with the new link
    store = await context.get_store()
    async with store.transaction() as conn:
        try:
            old_link, new_link = await update_scrobble_links(
                conn,
                scrobble_message.message_id,
                amender_user_id,
                amender.link_type,
                amender.link_key,
                new_link,
            )
        except PermissionError:
            logger.warning(f'user {amender_user_id} forbidden amend of {scrobble_message.message_id}')
            await update.message.delete()
            return

    new_markdown = scrobble_message.text_markdown_v2.replace(old_link, new_link)

    # ensure link preview is updated if needed
    link_preview_options = scrobble_message.link_preview_options
    if link_preview_options and link_preview_options.url == old_link:
        logger.debug(f'{old_link}={link_preview_options.url}, updating link preview url to {new_link}')
        link_preview_options = LinkPreviewOptions(
            url=new_link,
            prefer_large_media=True,
            show_above_text=True,
        )

    # edit the message with the new text
    await scrobble_message.edit_text(
        new_markdown,
        parse_mode=ParseMode.MARKDOWN_V2,
        link_preview_options=link_preview_options,
        reply_markup=scrobble_message.reply_markup,
    )
    logger.debug(f'amended scrobble {scrobble_message.message_id} with {amender.link_key}: {new_link}')

    # delete the original amend message to keep the chat clean
    await update.message.delete()
