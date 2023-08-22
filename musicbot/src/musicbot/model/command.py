import logging
from typing import Callable

from telegram.ext import Dispatcher, MessageHandler
from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.filters import MessageFilter
from telegram.update import Update


logger = logging.getLogger(__name__)


class Command:
    """Command class.

    Commands registered in the bot are instances of this class.

    :param name: Command name, the user must input this preceded by `!` to run
                 the command.
    :help_message: Help message shown when the user invokes `!help`.
    :filters: One or a combination of ``MessageFilter`` to trigger the command.
    :handler: A `Callable` which will run when the command is triggered.
    """

    def __init__(
        self,
        name: str,
        help_message: str,
        filters: MessageFilter,
        handler: Callable,
    ) -> None:
        self.name = name
        self.help_message = help_message
        self.filters = filters
        self.handler = handler

    def __str__(self) -> str:
        return f"[Command] {self.name}"

    def handle(self, update: Update, context: CallbackContext) -> None:
        # we don't care about edits
        if update.edited_message:
            return

        chat_id = update.message.chat_id
        message_id = update.message.message_id
        dj = f"@{update.message.from_user.username}"
        command = update.message.text

        logger.info(f"[chat_id: {chat_id}, msg_id: {message_id}]: user {dj}" f" issued [{command}]")

        self.handler(update, context)

    def register_handler(self, dispatcher: Dispatcher) -> None:
        dispatcher.add_handler(MessageHandler(self.filters, self.handle))
