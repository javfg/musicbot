import logging

from telegram.ext import Filters, Updater

from musicbot.config import config
from musicbot.handlers.handle_amend import HandleAmend
from musicbot.handlers.handle_chatid import HandleChatId
from musicbot.handlers.handle_digest import HandleDigest
from musicbot.handlers.handle_help import HandleHelp
from musicbot.handlers.handle_ranking import HandleRanking
from musicbot.handlers.handle_stats import HandleStats
from musicbot.handlers.handle_submission import HandleSubmission
from musicbot.handlers.handle_tag import HandleTag
from musicbot.model.command import Command
from musicbot.util.filters import ChatIdFilter, ReplyToBotFilter


logger = logging.getLogger(__name__)
commands = [
    Command(
        "amend",
        None,
        ReplyToBotFilter() & ChatIdFilter(),
        HandleAmend,
    ),
    Command(
        "digest",
        (
            "Shows a digest of the `month`, `week` or `day`\\. For example, to see the submissions  "
            "of the week, send: `\\!digest week`\\."
        ),
        Filters.regex("^!digest\\s?(|day|week|month)$") & ChatIdFilter(),
        HandleDigest,
    ),
    Command(
        "help",
        "Shows the help\\.",
        Filters.regex("^!help$") & ChatIdFilter(),
        HandleHelp,
    ),
    Command(
        "stats",
        "Shows users stats\\.",
        Filters.regex("^!stats\\s?[A-Za-z0-9_]*$") & ChatIdFilter(),
        HandleStats,
    ),
    Command(
        "ranking",
        (
            "Shows the submission ranking for the `month`, `week` or `day`\\. For example, to see "
            "the weekly ranking, send: `\\!ranking week`\\."
        ),
        Filters.regex("^!ranking\\s?(day|week|month)?$") & ChatIdFilter(),
        HandleRanking,
    ),
    Command(
        "tag",
        (
            "Shows music by tag\\. You can specify the amount of submissions to show by adding a "
            "number after, and another one to start showing submissions from an offset\\. For "
            "example: `\\!tag rock 5 37` will show 5 submissions with the tag `rock` starting from "
            "submission number 38\\."
        ),
        Filters.regex("^!tag [A-Za-z0-9_#]+\\s?[0-9]*\\s?[0-9]*$") & ChatIdFilter(),
        HandleTag,
    ),
    Command(
        "submission",
        None,
        Filters.regex("^!(?!amend|digest|help|stats|ranking|tag|chatid).+") & ChatIdFilter(),
        HandleSubmission,
    ),
    Command(
        "chatid",
        None,
        Filters.regex("^!chatid"),
        HandleChatId,
    ),
]


def main() -> None:
    bot_name = config.get("BOT_NAME")
    telegram_client_id = config["TELEGRAM_CLIENT_ID"]
    telegram_client_secret = config["TELEGRAM_CLIENT_SECRET"]
    # register bot
    telegram_token = f"{telegram_client_id}:{telegram_client_secret}"

    updater = Updater(telegram_token)
    dispatcher = updater.dispatcher

    # handlers
    for command in commands:
        command.register_handler(dispatcher)

    # start loop
    updater.start_polling()
    logger.info(f"{bot_name} started")
    updater.idle()


if __name__ == "__main__":
    main()
