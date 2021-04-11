from datetime import datetime
from typing import Optional

from musicbot.model.submission import Submission
from musicbot.model.submissionType import SubmissionType
from musicbot.utils import _


class Album(Submission):
    """TODO: fill this"""

    def __init__(
        self,
        artist: Optional[str] = None,
        artist_url: Optional[str] = None,
        album: Optional[str] = None,
        album_url: Optional[str] = None,
        genre_tags: Optional[list[str]] = [],
        release_date: Optional[datetime] = None,
    ) -> None:
        super().__init__(type=SubmissionType.album)

        self.artist = artist
        self.artist_url = artist_url
        self.album = album
        self.album_url = album_url
        self.genre_tags = genre_tags
        self.release_date = release_date
        self.dj = None

    def __str__(self) -> str:
        return f"[track] {self.artist} - {self.album}"

    def to_md(self) -> str:
        genre_tags_str = ", ".join([f"{genre}" for genre in self.genre_tags])
        title_line = f"{_(self.artist)} \\- [{_(self.album)}]({_(self.album_url)})"
        if self.release_date:
            title_line += f" \\(\\#released\\_{_(self.release_date.strftime('%Y'))}\\)"
        artist_line = f"*Artist:* [{_(self.artist)}]({_(self.artist_url)})"

        return f"""
{title_line}
\\({_(self.type.value)} sent by @{_(self.dj)}\\)

*Tags:* {_(genre_tags_str)}

{artist_line}
        """
