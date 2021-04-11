#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

from telegram.ext import Filters, MessageHandler, Updater

from musicbot.config import config
from musicbot.handlers.handle_amend import handle_amend
from musicbot.handlers.handle_help import handle_help
from musicbot.handlers.handle_submission import handle_submission

logger = logging.getLogger(__name__)


def main() -> None:
    # init db

    # register bot
    telegram_token = f"{config['TELEGRAM_CLIENT_ID']}:{config['TELEGRAM_CLIENT_SECRET']}"

    updater = Updater(telegram_token)
    dispatcher = updater.dispatcher

    # handlers
    dispatcher.add_handler(MessageHandler(Filters.regex("^!help$"), handle_help))
    dispatcher.add_handler(MessageHandler(Filters.regex("^!"), handle_submission))
    dispatcher.add_handler(MessageHandler(Filters.reply, handle_amend))

    # start loop
    updater.start_polling()
    logger.info(f"{config['BOT_NAME']} started")
    updater.idle()


if __name__ == "__main__":
    main()
