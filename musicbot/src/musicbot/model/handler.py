import logging

from telegram.ext.callbackcontext import CallbackContext
from telegram.update import Update

from musicbot.config import db_manager
from musicbot.model.messageactionsmixin import MessageActionsMixin


class Handler(MessageActionsMixin):
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
