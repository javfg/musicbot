from itertools import groupby
from typing import List, Tuple

from telegram.ext.callbackcontext import CallbackContext
from telegram.update import Update

from musicbot.model.handler import Handler
from musicbot.model.scheduler import Scheduler
from musicbot.model.submission import Submission
from musicbot.util import _, get_timeframe
from musicbot.util.db import DB


RANK_COUNT = 10


class HandleRanking(Handler):
    def __init__(self, update: Update, context: CallbackContext) -> None:
        super().__init__(update, context)
        self.message_timeframe = self.getCommandArgs(1, "infinity")
        self.handle()

    def handle(self) -> None:
        t_start = get_timeframe(self.message_timeframe)
        submissions = self.db.get_submissions_by_date(t_start)
        ranking = calculate_ranking(submissions)
        message = create_ranking_message(ranking, self.message_timeframe)
        self.send_message(message, disable_web_page_preview=True)


class MonthlyRanking(Scheduler):
    def __init__(self, context: CallbackContext) -> None:
        super().__init__(context)

    def run(self, db: DB) -> None:
        t_start = get_timeframe("month")
        submissions = db.get_submissions_by_date(t_start)
        ranking = calculate_ranking(submissions)
        message = create_ranking_message(ranking, "month")
        self.send_message(message, disable_web_page_preview=True)


def calculate_ranking(submissions: List[Submission]):
    return sorted(
        [(dj, len(list(grouper))) for dj, grouper in groupby(submissions, lambda x: x.dj)],
        key=lambda x: x[1],
        reverse=True,
    )[:RANK_COUNT]


def create_ranking_message(djs: List[Tuple[int, str]], caption: str) -> str:
    trophies = ["🥇 1\\.", "🥈 2\\.", "🥉 3\\.", *[f"➖ {n + 4}\\." for n in range(RANK_COUNT)]]
    if caption == "infinity":
        message = "*🏆 All\\-time submission ranking*:\n"
    else:
        message = f"*🏆 Submission ranking for the {caption}*:\n"
    if not djs:
        message += "\nNothing so far\\.\\.\\. 😞"
    for index, dj in enumerate(djs):
        message += f"\n{trophies[index]} {_(dj[0])}: {_(str(dj[1]))}"
    return message
