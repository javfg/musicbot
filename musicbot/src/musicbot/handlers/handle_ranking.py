from itertools import groupby
from typing import List, Tuple

from telegram.ext.callbackcontext import CallbackContext
from telegram.update import Update

from musicbot.model.handler import Handler
from musicbot.util import _, timeframes


class HandleRanking(Handler):
    def __init__(self, update: Update, context: CallbackContext) -> None:
        super().__init__(update, context)
        self.message_timeframe = self.command[1] or "infinity"
        self.rank_count = 10
        self.handle()

    def handle(self) -> None:
        timeframe_start = timeframes[self.message_timeframe]()
        results = self.db.get_submissions_since(timeframe_start)
        ranking = sorted(
            [(dj, len(list(grouper))) for dj, grouper in groupby(results, lambda x: x.dj)],
            key=lambda x: x[1],
            reverse=True,
        )[: self.rank_count]
        messages = self.create_ranking_message(ranking)
        self.send_message(messages, disable_web_page_preview=True)

    def create_ranking_message(self, djs: List[Tuple[int, str]]) -> str:
        trophies = ["🥇 1\\.", "🥈 2\\.", "🥉 3\\.", *[f"➖ {n + 4}\\." for n in range(self.rank_count - 3)]]
        if self.message_timeframe == "infinity":
            message = "*🏆 All\\-time submission ranking*:\n"
        else:
            message = f"*🏆 Submission ranking for the {self.message_timeframe}*:\n"
        if not djs:
            message += "\nNothing so far\\.\\.\\. 😞"
        for index, dj in enumerate(djs):
            message += f"\n{trophies[index]} {_(dj[0])}: {_(str(dj[1]))}"
        return message
