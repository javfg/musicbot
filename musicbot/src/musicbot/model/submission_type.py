from enum import Enum


class SubmissionType(Enum):
    """Submission Type enum.

    Represents the type of a submission, which, being music,
    can be either an artist, album or track.
    """

    empty = "empty"
    artist = "artist"
    album = "album"
    track = "track"
