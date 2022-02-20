from telegram import Update
from telegram.ext import CallbackContext

from musicbot.model.handler import Handler
from musicbot.util import _


class HandleChatId(Handler):
    def __init__(self, update: Update, context: CallbackContext) -> None:
        super().__init__(update, context)
        self.handle()

    def handle(self) -> None:
        self.send_message(_(str(self.chat_id)))
