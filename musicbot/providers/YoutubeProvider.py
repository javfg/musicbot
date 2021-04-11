import logging

from musicbot.model.provider import Provider
from musicbot.model.track import Track
from musicbot.providers.youtube.fetchers import youtube_fetch
from musicbot.providers.youtube.uris import validate_uri
from musicbot.utils import SpotifyEntityNotFoundException, YoutubeMetadataNotFoundException

logger = logging.getLogger(__name__)


class YoutubeProvider(Provider):
    def __init__(self, uri: str) -> None:
        self.data = Track()
        self.data.track_youtube_url = uri

        if validate_uri(uri):
            self.uri = uri

    def fetch(self) -> None:
        logger.info(f"fetching data for youtube video with uri: {self.uri}")

        try:
            self.data = youtube_fetch(self.uri)

        except (YoutubeMetadataNotFoundException, SpotifyEntityNotFoundException):
            self.data.not_found = True
            pass
