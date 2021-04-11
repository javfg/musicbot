from datetime import datetime
from typing import Optional

from musicbot.model.submission import Submission
from musicbot.model.submissionType import SubmissionType
from musicbot.utils import _


class Artist(Submission):
    """TODO: fill this"""

    def __init__(
        self,
        artist: Optional[str] = None,
        artist_url: Optional[str] = None,
        genre_tags: Optional[list[str]] = [],
    ) -> None:
        super().__init__(type=SubmissionType.artist)

        self.artist = artist
        self.artist_url = artist_url
        self.genre_tags = genre_tags
        self.dj = None

    def __str__(self) -> str:
        return f"[track] {self.artist}"

    def to_md(self) -> str:
        genre_tags_str = ", ".join([f"{genre}" for genre in self.genre_tags])
        title_line = f"[{_(self.artist)}]({_(self.artist_url)})"

        return f"""
{title_line}
\\({_(self.type.value)} sent by @{_(self.dj)}\\)

*Tags:* {_(genre_tags_str)}
            """
