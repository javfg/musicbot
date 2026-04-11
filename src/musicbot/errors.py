import traceback

from loguru import logger
from telegram import Update
from telegram.error import NetworkError

from musicbot.context import MusicbotContext


async def error_handler(update: object, context: MusicbotContext) -> None:
    if context.error is None:
        logger.error('error handler called without an error')
        return

    if isinstance(context.error, NetworkError):
        logger.warning(f'network error: {context.error}')
        return

    logger.opt(exception=context.error).error('exception while handling an update')

    chat_id_errors = context.config.chat_id_errors
    if not chat_id_errors:
        return

    # build traceback info
    tb = ''.join(traceback.format_exception(None, context.error, context.error.__traceback__))

    # send error details to the error log channel
    if isinstance(update, Update):
        user = update.effective_user
        chat = update.effective_chat
        user_info = f'user: {user.full_name} (@{user.username}, id: {user.id})' if user else 'user: N/A'

        if chat:
            chat_info = f'chat: {chat.title or chat.type} (id: {chat.id})'
        elif update.inline_query:
            chat_info = f'chat: inline query ("{update.inline_query.query}")'
        else:
            chat_info = 'chat: N/A'
    else:
        user_info = 'user: N/A'
        chat_info = 'chat: N/A'

    message = (
        f'⚠️ <b>an error occurred</b>\n\n'
        f'{user_info}\n'
        f'{chat_info}\n\n'
        f'<b>error:</b> {type(context.error).__name__}: {context.error}\n\n'
        f'<b>traceback:</b>\n<pre>{tb[:3000]}</pre>'  # Telegram has a 4096 char limit
    )

    await context.bot.send_message(chat_id=chat_id_errors, text=message, parse_mode='HTML')
