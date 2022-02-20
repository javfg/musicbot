import logging.config
import os

from datetime import datetime


class fullNameFilter(logging.Filter):
    def filter(self, record):
        record.full_name = "{}:{}".format(record.name, record.funcName)
        return True


def logger_init(bot_name):
    log_file_date = datetime.now().strftime("%Y-%m-%d-%H-%M")
    LOG_SETTINGS = {
        "version": 1,
        "filters": {
            "full_name_filter": {
                "()": fullNameFilter,
            },
        },
        "formatters": {
            "standard": {
                "format": "%(asctime)s %(levelname)-8s [%(full_name)-55s] %(message)s",
            }
        },
        "handlers": {
            "default": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "filters": ["full_name_filter"],
                "formatter": "standard",
            }
        },
        "loggers": {
            "musicbot": {
                "handlers": ["default"],
                "level": "DEBUG",
            },
            "apscheduler": {
                "handlers": ["default"],
                "level": "INFO",
            },
            "telegram": {
                "handlers": ["default"],
                "level": "INFO",
            },
            "youtube_dl": {
                "handlers": ["default"],
                "level": "INFO",
            },
        },
    }

    file_handler = {
        "level": "DEBUG",
        "class": "logging.handlers.RotatingFileHandler",
        "filters": ["full_name_filter"],
        "formatter": "standard",
        "filename": f"logs/{bot_name}-{log_file_date}.log",
        "mode": "a",
        "maxBytes": 10485760,
        "backupCount": 5,
    }

    if os.getenv("MUSICBOT_ENV") == "prod" or os.getenv("LOGTOFILE"):
        LOG_SETTINGS["handlers"]["file"] = file_handler
        for logger in LOG_SETTINGS["loggers"].keys():
            LOG_SETTINGS["loggers"][logger]["handlers"].append("file")

    logging.config.dictConfig(LOG_SETTINGS)
