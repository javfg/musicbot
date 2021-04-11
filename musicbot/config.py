import logging
import os
import sqlite3
from datetime import datetime

import youtube_dl
from spotipy.client import Spotify
from spotipy.oauth2 import SpotifyClientCredentials

config = {
    **os.environ,
}

# spotify provider
spotipy_provider = Spotify(
    client_credentials_manager=SpotifyClientCredentials(
        client_id=config["SPOTIPY_CLIENT_ID"],
        client_secret=config["SPOTIPY_CLIENT_SECRET"],
    )
)

# youtube_dl config & provider
ydl_opts = {
    "quiet": True,
    "skip_download": True,
    "forceid": True,
}

ydl_provider = youtube_dl.YoutubeDL(ydl_opts)

# logging config
log_file_date = datetime.now().strftime("%Y-%m-%d-%H-%M")
logging.basicConfig(
    format="[%(asctime)s %(name)40s] - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler(f"./logs/{config['BOT_NAME']}-{log_file_date}.log"),
        logging.StreamHandler(),
    ],
)

# db
db = sqlite3.connect("./db/data.db")
