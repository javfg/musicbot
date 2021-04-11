import logging
from datetime import datetime
from typing import Callable

from spotipy import SpotifyException

from musicbot.config import spotipy_provider
from musicbot.model.album import Album
from musicbot.model.artist import Artist
from musicbot.model.submission import Submission
from musicbot.model.submissionType import SubmissionType
from musicbot.model.track import Track
from musicbot.providers.youtube.uris import uri_from_title
from musicbot.utils import SpotifyEntityNotFoundException, escape_genre

logger = logging.getLogger(__name__)


def parse_date(release_date: str) -> datetime:
    # we don't care about no stinking precision!
    return datetime.fromisoformat(f"{release_date.split('-')[0]}-01-01")


def get_fetch_strategy(entity: SubmissionType) -> Callable:
    fetch_strategies = {
        SubmissionType.track: fetch_track,
        SubmissionType.album: fetch_album,
        SubmissionType.artist: fetch_artist,
    }

    return fetch_strategies[entity]


def fetch_artist(artist_id: str) -> Artist:
    try:
        artist_data = spotipy_provider.artist(artist_id)

    except SpotifyException as error:
        logger.error(error.msg)
        raise SpotifyEntityNotFoundException

    return Artist(
        artist=artist_data["name"],
        artist_url=artist_data["external_urls"]["spotify"],
        genre_tags=[f"#{escape_genre(genre)}" for genre in artist_data["genres"]],
    )


def fetch_album(album_id: str) -> Album:
    try:
        album_data = spotipy_provider.album(album_id)
        artist_data = spotipy_provider.artist(album_data["artists"][0]["id"])

    except SpotifyException as error:
        logger.error(error.msg)
        raise SpotifyEntityNotFoundException

    return Album(
        artist=album_data["artists"][0]["name"],
        artist_url=album_data["artists"][0]["external_urls"]["spotify"],
        album=album_data["name"],
        album_url=album_data["external_urls"]["spotify"],
        genre_tags=[f"#{escape_genre(genre)}" for genre in artist_data["genres"]],
        release_date=parse_date(album_data["release_date"]),
    )


def fetch_track(track_id: str) -> Track:
    try:
        track_data = spotipy_provider.track(track_id)
        artist_data = spotipy_provider.artist(track_data["artists"][0]["id"])

    except SpotifyException as error:
        logger.error(error.msg)
        raise SpotifyEntityNotFoundException

    artist = track_data["artists"][0]["name"]
    track = track_data["name"]
    track_youtube_url = uri_from_title(artist, track)

    return Track(
        artist=artist,
        artist_url=track_data["artists"][0]["external_urls"]["spotify"],
        album=track_data["album"]["name"],
        album_url=track_data["album"]["external_urls"]["spotify"],
        track=track,
        track_url=track_data["external_urls"]["spotify"],
        track_youtube_url=track_youtube_url,
        genre_tags=[f"#{escape_genre(genre)}" for genre in artist_data["genres"]],
        release_date=parse_date(track_data["album"]["release_date"]),
    )


def spotify_fetch(uri: str, entity: SubmissionType = SubmissionType.track) -> Submission:
    fetch_strategy = get_fetch_strategy(entity)

    try:
        result = fetch_strategy(uri)

        logger.info(f"successfully fetched spotify {result}")

        return result

    except SpotifyException as error:
        logger.error(error.msg)
        raise SpotifyEntityNotFoundException
