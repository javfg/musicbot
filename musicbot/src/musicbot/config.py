import logging
import os

import youtube_dl

from spotipy import Spotify, SpotifyClientCredentials

from musicbot.util.db import DBManager
from musicbot.util.logger import logger_init


config = {
    **os.environ,
    "VALID_CHAT_IDS": [int(chat_id) for chat_id in list(filter(None, os.environ.get("VALID_CHAT_IDS", "").split(",")))],
    "AMEND_SAME_USER": False,
}

# logger
logger_init(config["BOT_NAME"])

# spotify provider
spotipy_provider = Spotify(
    client_credentials_manager=SpotifyClientCredentials(
        client_id=config["SPOTIPY_CLIENT_ID"],
        client_secret=config["SPOTIPY_CLIENT_SECRET"],
    )
)

# create required folders for db & logs
os.makedirs("./db", exist_ok=True)
os.makedirs("./logs", exist_ok=True)

# youtube_dl config & provider
ydl_opts = {
    "quiet": True,
    "skip_download": True,
    "forceid": True,
    "logger": logging.getLogger("youtube_dl"),
}
ydl_provider = youtube_dl.YoutubeDL(ydl_opts)

# db
db_manager = DBManager(config["VALID_CHAT_IDS"])
