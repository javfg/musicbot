from telegram.ext.callbackcontext import CallbackContext
from telegram.update import Update

from musicbot.model.handler import Handler
from musicbot.model.submission import Submission
from musicbot.util import _
from musicbot.util.util import split_message


MAX_TAGS_PER_REQUEST = 20


class HandleTag(Handler):
    def __init__(self, update: Update, context: CallbackContext) -> None:
        super().__init__(update, context)
        _, tag, limit, offset, *rest = self.command
        self.tag = f"#{tag}" if tag[0] != "#" else tag
        self.limit = min(int(limit or 10), MAX_TAGS_PER_REQUEST)
        self.offset = int(offset or 0)
        self.original_offset = offset
        self.showing_last = False
        self.handle()

    def handle(self) -> None:
        results = self.db.get_submissions_by_tag(self.tag)
        if self.offset > len(results):
            self.showing_last = True
            self.offset = max(0, len(results) - self.limit)
        results = results[self.offset : self.offset + self.limit]
        messages = split_message(self.create_tag_message(results))
        self.send_messages(messages, disable_web_page_preview=True)

    def create_tag_message(self, submissions: list[Submission]) -> str:
        message = f"*🏷️ Stuff tagged with {_(self.tag)}*"
        if not len(submissions):
            message += "\nNothing so far\\.\\.\\. 😞"
            return message
        if self.offset or self.showing_last:
            message += f", offset {self.offset}"
        if self.showing_last:
            message += ", showing the last entries"
        message += ":\n\n"
        message += ("\n").join([s.to_inline_md(index + 1 + self.offset) for index, s in enumerate(submissions)])
        return message
