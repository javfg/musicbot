from collections import Counter
from typing import List, Tuple

from telegram.ext.callbackcontext import CallbackContext
from telegram.update import Update

from musicbot.model.handler import Handler
from musicbot.model.submission import Submission
from musicbot.util.util import _


class HandleStats(Handler):
    def __init__(self, update: Update, context: CallbackContext) -> None:
        super().__init__(update, context)
        self.dj = self.command[1] or update.message.from_user.username
        self.fav_tags_count = 3
        self.handle()

    def handle(self) -> None:
        results = self.db.get_submissions_for_dj(self.dj)
        tags = [tag for result in results for tag in result.artist_genre_tags]
        fav_tags = sorted(list(Counter(tags).items()), key=lambda x: x[1], reverse=True)[: self.fav_tags_count]
        message = self.create_stats_message(results, fav_tags, len(set(tags)))
        self.send_message(message, disable_web_page_preview=True)

    def create_stats_message(
        self,
        submissions: List[Submission],
        fav_tags: List[Tuple[int, str]],
        tag_count: int,
    ) -> str:
        message = f"*📈 Stats for DJ @{self.dj}:*\n\n"
        if not submissions:
            message += "Nothing so far\\.\\.\\. 😞"
        else:
            message += f"*🎵 Submissions:* {len(submissions)}\n"
            message += "*🏷️ Favorite tags:*"
            for index, tag in enumerate(fav_tags):
                message += f"\n        {index + 1}\\. {_(tag[0])} \\({str(tag[1])}\\)"
            message += f"\n*🌈 Different tags:* {str(tag_count)}"
        return message
