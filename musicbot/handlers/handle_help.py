import logging

from telegram.ext.callbackcontext import CallbackContext
from telegram.parsemode import ParseMode
from telegram.update import Update
from telegram.utils.helpers import escape_markdown

logger = logging.getLogger(__name__)


def handle_help(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    message_id = update.message.message_id
    message_author = f"@{update.message.from_user.username}"

    logger.info(f"[{message_author}, {message_id}]")

    help_msg = f"""
Hi\!

Paste a \! followed by a youtube url or spotify url \/ uri and I will find info about the track for you\.

Just like this\: \!{escape_markdown('https://www.youtube.com/watch?v=5NV6Rdv1a3I' ,2)}

Some times I won't be able to find out the info, you can help me by replying to my message with the track title and artist\.
    """

    context.bot.send_message(
        chat_id=chat_id, text=help_msg, parse_mode=ParseMode.MARKDOWN_V2, disable_web_page_preview=True
    )
