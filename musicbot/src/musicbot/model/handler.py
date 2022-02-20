import logging

from typing import List

from telegram import Message, ParseMode
from telegram.ext.callbackcontext import CallbackContext
from telegram.update import Update

from musicbot.config import db_manager


class Handler:
    def __init__(self, update: Update, context: CallbackContext) -> None:
        self.update = update
        self.context = context
        self.logger = logging.getLogger(__name__)
        self.chat_id = update.message.chat_id
        self.message_id = update.message.message_id
        self.dj = update.message.from_user.username
        self.db = db_manager.get_db(self.chat_id)
        self.command = f"{update.message.text}      ".split(" ")

    def handle(self) -> None:
        pass

    def send_message(self, message: str, **kwargs) -> List[Message]:
        return self.context.bot.send_message(
            chat_id=self.chat_id,
            text=message,
            parse_mode=ParseMode.MARKDOWN_V2,
            **kwargs,
        )

    def send_messages(self, messages: List[str], **kwargs) -> Message:
        sent_messages = []
        for message in messages:
            sent_messages.append(self.send_message(message, **kwargs))
        return sent_messages

    def delete_message(self, **kwargs) -> bool:
        return self.context.bot.delete_message(**kwargs)

    def delete_messages(self, message_ids: List[int]) -> None:
        deleted_messages = []
        for message_id in message_ids:
            deleted_messages.append(self.context.bot.delete_message(chat_id=self.chat_id, message_id=message_id))
        return deleted_messages
