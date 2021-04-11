import logging

from telegram.ext.callbackcontext import CallbackContext
from telegram.parsemode import ParseMode
from telegram.update import Update

from musicbot.config import config
from musicbot.providers.spotifyProvider import SpotifyProvider
from musicbot.utils import SpotifyEntityNotFoundException

logger = logging.getLogger(__name__)


def handle_amend(update: Update, context: CallbackContext) -> None:
    if (
        "has no metadata!" in update.message.reply_to_message.text
        and update.message.reply_to_message.from_user.username == config["BOT_USERNAME"]
    ):
        amend_not_found(update, context)


def amend_not_found(update: Update, context: CallbackContext) -> None:
    # lets change this shit
    amended_msg = update.message.reply_to_message
    amended_id = amended_msg.message_id
    amended_username = amended_msg.text.split("submitted by ")[1].split(" has no metadata")[0]
    amend_username = update.message.from_user.username
    chat_id = update.message.chat_id
    amend_id = update.message.message_id
    amend = update.message.text

    logger.info(
        f"[{amend_username}, {amend_id}] sent amend for [{amended_username} {amended_id}]: {amend}"
    )

    try:
        provider = SpotifyProvider(title=amend)
        provider.fetch()

    except SpotifyEntityNotFoundException:
        context.bot.delete_message(chat_id=chat_id, message_id=amend_id)
        return

    provider.set_dj(amended_username)

    amended_msg.edit_text(text=provider.to_md(), parse_mode=ParseMode.MARKDOWN_V2)
    context.bot.delete_message(chat_id=chat_id, message_id=amend_id)
