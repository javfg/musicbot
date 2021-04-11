import logging
from re import match
from typing import Tuple

from spotipy.exceptions import SpotifyException

from musicbot.config import spotipy_provider
from musicbot.utils import InvalidUriException, SpotifyEntityNotFoundException

logger = logging.getLogger(__name__)
spotify_regex = r"^(spotify:|https://open\.spotify\.com/)(track|album|artist)"


def validate_uri(uri: str) -> bool:
    return match(spotify_regex, uri)


def parse_uri(uri: str) -> Tuple[str, str]:
    uri_match = match(spotify_regex, uri)

    if uri_match:
        spotify_entity = uri_match[2]

        logger.info(f"valid spotify [{spotify_entity}] uri: {uri}")

        return uri, spotify_entity

    else:
        logger.error(f"invalid spotify uri: {uri}")

        raise InvalidUriException


def uri_from_title(title: str) -> str:
    try:
        spotify_search_results = spotipy_provider.search(title, limit=1, type="track")

    except SpotifyException as error:
        logger.error(error.msg)
        raise SpotifyEntityNotFoundException

    if not len(spotify_search_results["tracks"]["items"]):
        logger.error(f"no results found for [{title}]")
        raise SpotifyEntityNotFoundException

    spotify_uri = spotify_search_results["tracks"]["items"][0]["uri"]

    logger.info(f"found spotify uri using [{title}]: [{spotify_uri}]")

    return spotify_uri
