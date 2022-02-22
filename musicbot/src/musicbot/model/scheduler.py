import logging

from telegram.ext.callbackcontext import CallbackContext

from musicbot.config import config, db_manager
from musicbot.model.message_actions_mixin import MessageActionsMixin
from musicbot.util.db import DB


class Scheduler(MessageActionsMixin):
    def __init__(self, context: CallbackContext) -> None:
        self.context = context
        self.chat_ids = config.get("VALID_CHAT_IDS", [])
        self.logger = logging.getLogger(__name__)

        for chat_id in self.chat_ids:
            db = db_manager.get_db(chat_id)
            self.chat_id = chat_id
            self.run(db)

    def run(self, db: DB) -> None:
        pass
