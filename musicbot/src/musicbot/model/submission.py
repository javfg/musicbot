from datetime import datetime
from textwrap import dedent
from typing import Optional, Union

from musicbot.model.submission_type import SubmissionType
from musicbot.util import _


class Submission:
    """The Submission class.

    This class represent a submission (artist, album or track).

    :param dj: The name of the user who made the submission.
    :param submission_date: The date the submission was made.
    :param submission_type: Type of submission (see :class:`SubmissionType
                            <musicbot.models.SubmissionType>`.).
    :param artist_name: The artist's name.
    :param artist_url: The artist's Spotify URL.
    :param artist_genre_tags: The genre tags, provided in a list.
    :param album_name: The album's name.
    :param album_url: The album's Spotify URL.
    :param album_release_date: The album's release date (only the year is relevant).
    :param track_name: The track's name.
    :param track_url: The track's Spotify URL.
    :param track_url_youtube: The track's Youtube URL.
    """

    def __init__(
        self,
        dj: str,
        submission_date: datetime = datetime.now(),
        submission_type: SubmissionType = SubmissionType.empty,
        artist_name: Optional[str] = None,
        artist_url: Optional[str] = None,
        artist_genre_tags: Optional[list[str]] = None,
        album_name: Optional[str] = None,
        album_url: Optional[str] = None,
        album_release_date: Optional[datetime] = None,
        track_name: Optional[str] = None,
        track_url: Optional[str] = None,
        track_url_youtube: Optional[str] = None,
    ) -> None:
        self.dj = dj
        self.submission_date = submission_date
        self.submission_type = submission_type
        self.artist_name = artist_name
        self.artist_url = artist_url
        self.artist_genre_tags = artist_genre_tags or []
        self.album_name = album_name
        self.album_url = album_url
        self.album_release_date = album_release_date
        self.track_name = track_name
        self.track_url = track_url
        self.track_url_youtube = track_url_youtube

    def __str__(self) -> str:
        return f"[{self.submission_type.value}]"

    def to_md(self) -> str:
        subtitle = f"\\({_(self.submission_type.value)} sent by @{_(self.dj)}\\)"
        tags_str = ", ".join([f"{tag}" for tag in self.artist_genre_tags])
        tags = f"*🏷️ Tags:* {_(tags_str)}"
        artist_line = album_line = track_line = album_release = ""

        if self.submission_type in [SubmissionType.track, SubmissionType.album]:
            artist_line = f"*👩‍🎤 Artist:* [{_(self.artist_name)}]({_(self.artist_url)})"

        if self.submission_type == SubmissionType.track:
            title = f"🎵 {_(self.artist_name)} \\- [{_(self.track_name)}]({_(self.track_url_youtube or self.track_url)})"
            if self.album_release_date:
                album_release = f" \\(\\#released\\_{_(self.album_release_date.strftime('%Y'))}\\)"
            track_line = f"*🎵 Track:* [{_(self.track_name)}]({_(self.track_url)})"
            album_line = f"*💿 Album:* [{_(self.album_name)}]({_(self.album_url)}) {album_release}"

        elif self.submission_type == SubmissionType.album:
            title = f"💿 {_(self.artist_name)} \\- [{_(self.album_name)}]({_(self.album_url)})"
            if self.album_release_date:
                title += f" \\(\\#released\\_{_(self.album_release_date.strftime('%Y'))}\\)"

        elif self.submission_type == SubmissionType.artist:
            title = f"👩‍🎤 [{_(self.artist_name)}]({_(self.artist_url)})"

        return dedent(
            f"""
                {title}
                {subtitle}

                {tags}

                {artist_line}
                {album_line}
                {track_line}
            """
        )

    def to_inline_md(self, index: Union[str, int] = "•") -> str:
        bullet = f"{_(str(index))}\\." if type(index) == int else index
        message = f"{bullet} *_DJ @{_(self.dj)}_*: [{_(self.artist_name)}]({_(self.artist_url)})"

        if self.submission_type == SubmissionType.artist:
            message += " \\(_artist_\\)"
        elif self.submission_type == SubmissionType.track:
            message += (
                f" \\- [{_(self.album_name)}]({_(self.album_url)}) \\- [{_(self.track_name)}]({_(self.track_url)})"
            )
            if yt_url := self.track_url_youtube:
                message += f" \\([Youtube]({_(yt_url)})\\)"
        elif self.submission_type == SubmissionType.album:
            message += f" \\- [{_(self.album_name)}]({_(self.album_url)}) \\(_album_\\)"

        return message
