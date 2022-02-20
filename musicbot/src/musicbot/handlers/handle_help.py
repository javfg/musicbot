from telegram.ext.callbackcontext import CallbackContext
from telegram.update import Update

from musicbot.config import config
from musicbot.model.handler import Handler
from musicbot.util import _


class HandleHelp(Handler):
    def __init__(self, update: Update, context: CallbackContext) -> None:
        super().__init__(update, context)
        self.bot_name = config.get("BOT_NAME", "")
        self.handle()

    def handle(self) -> None:
        from musicbot.musicbot import commands

        help_items = "\n".join(
            [(f"*\\!{_(command.name)}*: {command.help_message}\n") for command in commands if command.help_message]
        )

        help_msg = (
            f"Hi\\! I\\'m *{_(self.bot_name)}*, your personal DJ\\! Send a song, album or artist by writing "
            "an exclamation mark `\\!` followed by the URL for a YouTube video or a spotify link or "
            "URI\\. I can do a lot of stuff, just send me instructions in the chat by writing one of the "
            f"following commands:\n\n{help_items}"
        )

        self.send_message(help_msg)
