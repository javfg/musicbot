import logging
from datetime import datetime
from re import match
from typing import Callable, Optional

from spotipy.exceptions import SpotifyException

from musicbot.config import spotipy_provider, ydl_provider
from musicbot.model.submission import Submission
from musicbot.model.submission_type import SubmissionType
from musicbot.util import escape_genre, parse_release_date
from musicbot.util.exceptions import SpotifyEntityNotFoundException, YoutubeMetadataNotFoundException


logger = logging.getLogger(__name__)

SPOTIFY_REGEX = r"^(:?spotify:|https://open\.spotify\.com/)(:?intl-[a-zA-Z]{2}/)?(?P<type>track|album|artist)[:/](?P<id>[A-Za-z0-9]{22})"
YOUTUBE_REGEX = r"^https://(www\.youtube\.com/watch\?v=|youtu\.be/)(?P<id>[A-Za-z0-9_-]{11})"


class Provider:
    def __init__(
        self,
        uri: Optional[str] = None,
        title: Optional[str] = None,
    ) -> None:
        self.uri = None
        self.url_youtube = None
        self.type = SubmissionType.empty
        self.title = title
        self.process_uri(uri)

    def process_uri(self, uri: str) -> str:
        if not uri and not self.title:
            return None

        if uri_match := match(SPOTIFY_REGEX, uri):
            # remove query params, we don't need them and sometimes they break spotipy
            self.uri = uri.split("?")[0]
            self.type = SubmissionType[uri_match.group("type")]
            logger.info(f"valid spotify uri: [{uri}]")
        elif match(YOUTUBE_REGEX, uri):
            song_name = self._youtube_name_from_uri(uri)
            self.url_youtube = uri
            self.uri = self._spotify_uri_from_name(song_name)
            self.type = SubmissionType.track
            logger.info(f"valid youtube uri: [{uri}]")
        elif self.title:
            # try with title
            self.uri = self._spotify_uri_from_name(self.title)
            self.type = SubmissionType.track
            logger.info(f"valid spotify uri from title [{self.title}]: [{self.uri}]")
        else:
            return None

    def _get_fetch_strategy(self, submission_type: SubmissionType) -> Callable:
        fetch_strategies = {
            SubmissionType.track: self._fetch_track,
            SubmissionType.album: self._fetch_album,
            SubmissionType.artist: self._fetch_artist,
        }
        return fetch_strategies[submission_type]

    def fetch(
        self,
        dj: str,
    ) -> Submission:
        fetch_strategy = self._get_fetch_strategy(self.type)
        result = fetch_strategy(self.uri, dj)
        logger.info(f"success [{self.uri}]: {result}")
        return result

    def _youtube_name_from_uri(self, uri: str) -> str:
        try:
            yt_metadata = ydl_provider.extract_info(uri, download=False)
            video_title = yt_metadata["title"]

            logger.info(f"success [{uri}]: [{video_title}]")
            return video_title

        except KeyError:
            logger.warn(f"failure [{uri}]: missing metadata")
            raise YoutubeMetadataNotFoundException
        except Exception as error:
            msg = getattr(error, "msg", error)
            logger.error(f"failure [{uri}]: {msg}")
            raise

    def _youtube_uri_from_name(self, name: str) -> Optional[str]:
        try:
            youtube_search = ydl_provider.extract_info(f"ytsearch:{name}")
            if youtube_search["entries"]:
                # grab first item in the search results and hope for the best!
                video_id = youtube_search["entries"][0]["id"]
                self.url_youtube = f"https://youtu.be/{video_id}"
                logger.info(f"success [{name}]: {self.url_youtube}")
        except Exception as error:
            logger.error(f"failure [{name}]: {error}")

    def _spotify_uri_from_name(self, name: str) -> Optional[str]:
        try:
            spotify_search = spotipy_provider.search(name, limit=1, type="track")
        except SpotifyException as error:
            logger.error(f"failure [{name}]: {error}")
            raise

        if not len(spotify_search["tracks"]["items"]):
            logger.error(f"failure [{name}]: no results")
            raise SpotifyEntityNotFoundException

        spotify_uri = spotify_search["tracks"]["items"][0]["uri"]
        logger.info(f"success [{name}]: [{spotify_uri}]")
        return spotify_uri

    def _fetch_artist(
        self,
        artist_id: str,
        dj: str,
    ) -> Submission:
        artist_data = spotipy_provider.artist(artist_id)

        return Submission(
            dj,
            datetime.now(),
            SubmissionType.artist,
            artist_name=artist_data["name"],
            artist_url=artist_data["external_urls"]["spotify"],
            artist_genre_tags=[f"#{escape_genre(genre)}" for genre in artist_data["genres"]],
        )

    def _fetch_album(
        self,
        album_id: str,
        dj: str,
    ) -> Submission:
        album_data = spotipy_provider.album(album_id)
        artist_data = spotipy_provider.artist(album_data["artists"][0]["id"])

        return Submission(
            dj,
            datetime.now(),
            SubmissionType.album,
            artist_name=album_data["artists"][0]["name"],
            artist_url=album_data["artists"][0]["external_urls"]["spotify"],
            artist_genre_tags=[f"#{escape_genre(genre)}" for genre in artist_data["genres"]],
            album_name=album_data["name"],
            album_url=album_data["external_urls"]["spotify"],
            album_release_date=parse_release_date(album_data["release_date"]),
        )

    def _fetch_track(
        self,
        track_id: str,
        dj: str,
    ) -> Submission:
        track_data = spotipy_provider.track(track_id)
        track_name = track_data["name"]
        artist_data = spotipy_provider.artist(track_data["artists"][0]["id"])
        artist_name = track_data["artists"][0]["name"]
        if not self.url_youtube:
            self._youtube_uri_from_name(f"{artist_name} {track_name} song")
        track_url_youtube = self.url_youtube

        return Submission(
            dj,
            datetime.now(),
            SubmissionType.track,
            artist_name=artist_name,
            artist_url=track_data["artists"][0]["external_urls"]["spotify"],
            artist_genre_tags=[f"#{escape_genre(genre)}" for genre in artist_data["genres"]],
            album_name=track_data["album"]["name"],
            album_url=track_data["album"]["external_urls"]["spotify"],
            album_release_date=parse_release_date(track_data["album"]["release_date"]),
            track_name=track_name,
            track_url=track_data["external_urls"]["spotify"],
            track_url_youtube=track_url_youtube,
        )
