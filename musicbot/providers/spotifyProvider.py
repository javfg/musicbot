import logging
from typing import Optional

from musicbot.model.provider import Provider
from musicbot.model.submission import Submission
from musicbot.model.submissionType import SubmissionType
from musicbot.providers.spotify.fetchers import spotify_fetch
from musicbot.providers.spotify.uris import parse_uri, uri_from_title, validate_uri
from musicbot.utils import InvalidUriException, SpotifyEntityNotFoundException

logger = logging.getLogger(__name__)


class SpotifyProvider(Provider):
    def __init__(self, uri: Optional[str] = None, title: Optional[str] = None) -> None:
        super().__init__()
        self.data = Submission()

        if uri and validate_uri(uri):
            try:
                (spotify_uri, spotify_entity) = parse_uri(uri)

            except InvalidUriException:
                pass

            self.uri = spotify_uri
            self.entity = SubmissionType[spotify_entity]

        elif title:
            try:
                spotify_uri = uri_from_title(title)
                self.uri = spotify_uri

            except InvalidUriException:
                pass

            self.uri = spotify_uri
            self.entity = SubmissionType.track

    def fetch(self) -> None:
        logger.info(f"fetching data for spotify [{self.entity.value}] with uri: {self.uri}")

        try:
            self.data = spotify_fetch(self.uri, self.entity)

        except SpotifyEntityNotFoundException:
            pass
