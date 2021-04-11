from telegram.utils.helpers import escape_markdown


def escape_genre(genre: str) -> str:
    return genre.replace(" ", "_").replace("-", "").replace("&", "_n_")


class SpotifyEntityNotFoundException(BaseException):
    pass


class YoutubeParserException(BaseException):
    pass


class YoutubeMetadataNotFoundException(BaseException):
    pass


class InvalidUriException(BaseException):
    pass


def _(str: str) -> str:
    return escape_markdown(str, 2)
