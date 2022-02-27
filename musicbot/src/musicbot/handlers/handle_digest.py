from telegram.ext.callbackcontext import CallbackContext
from telegram.update import Update

from musicbot.model.handler import Handler
from musicbot.model.scheduler import Scheduler
from musicbot.model.submission import Submission
from musicbot.util import get_timeframe, split_message
from musicbot.util.db import DB


class HandleDigest(Handler):
    def __init__(self, update: Update, context: CallbackContext) -> None:
        super().__init__(update, context)
        self.message_timeframe = self.command[1] or "week"
        self.handle()

    def handle(self) -> None:
        timeframe_start = get_timeframe(self.message_timeframe)
        results = self.db.get_submissions_by_date(timeframe_start)
        messages = split_message(create_digest_message(results, self.message_timeframe))
        self.send_messages(messages, disable_web_page_preview=True)


class DailyDigest(Scheduler):
    def __init__(self, context: CallbackContext) -> None:
        super().__init__(context)

    def run(self, db: DB) -> None:
        t_start, t_end = get_timeframe("yesterday")
        results = db.get_submissions_by_date(t_start, t_end)
        if not results:
            self.logger.info("skipping daily digest, no submissions yesterday")
            return
        messages = split_message(create_digest_message(results, "yesterday"))
        self.send_messages(messages)


class WeeklyDigest(Scheduler):
    def __init__(self, context: CallbackContext) -> None:
        super().__init__(context)

    def run(self, db: DB) -> None:
        t_start = get_timeframe("week")
        results = db.get_submissions_by_date(t_start)
        if not results:
            self.logger.info("skipping weekly digest, no submissions yesterday")
            return
        messages = split_message(create_digest_message(results, "week"))
        self.send_messages(messages)


def create_digest_message(submissions: list[Submission], caption: str) -> str:
    if caption in ["month", "week", "day"]:
        message = f"*📒 Digest for the {caption}:*\n"
    elif caption == "yesterday":
        message = "*📒 Yesterday's digest:*\n"
    if not len(submissions):
        message += "Nothing so far\\.\\.\\. 😞"
    message += ("\n").join([s.to_inline_md() for s in submissions])

    return message
