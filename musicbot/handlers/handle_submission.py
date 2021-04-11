import logging

from telegram import ParseMode
from telegram.ext.callbackcontext import CallbackContext
from telegram.update import Update

from musicbot.providers.spotifyProvider import SpotifyProvider
from musicbot.providers.YoutubeProvider import YoutubeProvider

logger = logging.getLogger(__name__)


def handle_submission(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    message_id = update.message.message_id
    message_author = update.message.from_user.username
    message_uri = update.message.text[1:]

    logger.info(f"[{message_author}, {message_id}] submission: {message_uri}")

    # right now only Spotify and youtube uris, maybe do this differently if that changes
    provider = None
    spotifyProvider = SpotifyProvider(message_uri)
    youtubeProvider = YoutubeProvider(message_uri)

    if spotifyProvider.has_valid_uri():
        provider = spotifyProvider
    elif youtubeProvider.has_valid_uri():
        provider = youtubeProvider
    else:
        return

    logger.info(f"{message_uri} is a valid uri, fetching...")
    provider.fetch()

    provider.set_dj(message_author)

    context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    context.bot.send_message(
        chat_id,
        text=provider.to_md(),
        parse_mode=ParseMode.MARKDOWN_V2,
        disable_web_page_preview=provider.is_not_found(),
    )
