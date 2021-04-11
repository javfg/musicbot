import logging

import youtube_dl

from musicbot.model.submission import Submission
from musicbot.model.submissionType import SubmissionType
from musicbot.providers.spotify.fetchers import spotify_fetch
from musicbot.providers.spotify.uris import uri_from_title
from musicbot.utils import SpotifyEntityNotFoundException, YoutubeMetadataNotFoundException

logger = logging.getLogger(__name__)


def get_video_title(uri):
    try:
        yt = youtube_dl.YoutubeDL({}).extract_info(uri, download=False)
        video_title = f"{yt['artist']} {yt['track']}"

        logger.info(f"found metadata in youtube uri [{uri}]: [{video_title}]")
        return video_title

    except KeyError:
        logger.warn(f"video [{uri}] has missing metadata!")
        raise YoutubeMetadataNotFoundException

    except Exception as error:  # take a look at youtube-dl exceptions
        logger.error(error.msg)
        raise


def youtube_fetch(uri: str) -> Submission:
    video_title = get_video_title(uri)

    try:
        spotify_uri = uri_from_title(video_title)

    except SpotifyEntityNotFoundException:
        raise

    return spotify_fetch(spotify_uri, SubmissionType.track)
