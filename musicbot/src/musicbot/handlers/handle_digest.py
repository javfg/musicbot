from telegram.ext.callbackcontext import CallbackContext
from telegram.update import Update

from musicbot.model.handler import Handler
from musicbot.model.submission import Submission
from musicbot.util import timeframes
from musicbot.util.util import date_title, split_message


class HandleDigest(Handler):
    def __init__(self, update: Update, context: CallbackContext) -> None:
        super().__init__(update, context)
        self.message_timeframe = self.command[1] or "week"
        self.handle()

    def handle(self) -> None:
        timeframe_start = timeframes[self.message_timeframe]()
        results = self.db.get_submissions_since(timeframe_start)
        messages = split_message(self.create_digest_message(results))
        self.send_messages(messages, disable_web_page_preview=True)

    def create_digest_message(self, submissions: list[Submission]) -> str:
        message = f"*📒 Digest for the {self.message_timeframe}* \\({date_title(self.message_timeframe)}\\):\n"
        if not len(submissions):
            message += "Nothing so far\\.\\.\\. 😞"
        message += ("\n").join([s.to_inline_md() for s in submissions])

        return message
