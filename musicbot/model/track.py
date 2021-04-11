from datetime import datetime
from typing import Optional

from musicbot.model.submission import Submission
from musicbot.model.submissionType import SubmissionType
from musicbot.utils import _


class Track(Submission):
    """TODO: fill this"""

    def __init__(
        self,
        artist: Optional[str] = None,
        artist_url: Optional[str] = None,
        album: Optional[str] = None,
        album_url: Optional[str] = None,
        track: Optional[str] = None,
        track_url: Optional[str] = None,
        track_youtube_url: Optional[str] = None,
        genre_tags: Optional[list[str]] = [],
        release_date: Optional[datetime] = None,
    ) -> None:
        super().__init__(type=SubmissionType.track)

        self.artist = artist
        self.artist_url = artist_url
        self.album = album
        self.album_url = album_url
        self.track = track
        self.track_url = track_url
        self.track_youtube_url = track_youtube_url
        self.genre_tags = genre_tags
        self.release_date = release_date
        self.dj = None

    def __str__(self) -> str:
        return f"[track] {self.artist} - {self.track}"

    def to_md(self) -> str:
        return self._to_md_not_found() if self.not_found else self._to_md()

    def _to_md_not_found(self) -> str:
        return f"""
*Youtube video* {_(self.track_youtube_url)} *submitted by* {_(self.dj)} *has no metadata\\!*

Reply to this message with either\\:
  • Spotify uri\\/link
  • Artist name and track just like you would search in Spotify
        """

    def _to_md(self) -> str:
        genre_tags_str = ", ".join([f"{genre}" for genre in self.genre_tags])
        title_url = self.track_youtube_url or self.track_url
        title_line = f"{_(self.artist)} \\- [{_(self.track)}]({_(title_url)})"
        artist_line = f"*Artist:* [{_(self.artist)}]({_(self.artist_url)})"
        album_line = f"*Album:* [{_(self.album)}]({_(self.album_url)})"
        if self.release_date:
            album_line += f" \\(\\#released\\_{_(self.release_date.strftime('%Y'))}\\)"
        track_line = f"*Track:* [{_(self.track)}]({_(self.track_url)})"

        return f"""
{title_line}
\\({_(self.type.value)} sent by @{_(self.dj)}\\)

*Tags:* {_(genre_tags_str)}

{artist_line}
{album_line}
{track_line}
            """
