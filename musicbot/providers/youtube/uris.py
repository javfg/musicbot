import logging
from re import match

from musicbot.config import ydl_provider

logger = logging.getLogger(__name__)
youtube_regex = r"^https://(www\.youtube\.com/watch\?v=|youtu\.be/)"


def validate_uri(uri: str) -> bool:
    if match(youtube_regex, uri):
        logger.info(f"valid youtube uri: {uri}")

        return True
    else:
        return False


def uri_from_title(artist: str, track: str) -> str:
    try:
        search = ydl_provider.extract_info(f"ytsearch:{artist} {track}")

        if search["entries"]:
            # # grab first item in the search results and hope for the best!
            video_id = search["entries"][0]["id"]
            video_link = f"https://youtu.be/{video_id}"
            logger.info(video_link)

            return video_link

        return None
    except Exception as error:
        logger.error(error)
        pass
