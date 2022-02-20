from musicbot.model.submission_type import SubmissionType
from musicbot.util import _


def subtitle_line(submission_type: SubmissionType, dj: str) -> str:
    return f"\\({_(submission_type.value)} sent by @{_(dj)}\\)"


def genre_line(genre_tags: list[str]) -> str:
    genre_str = ", ".join([f"{genre}" for genre in genre_tags])
    return f"*Tags:* {_(genre_str)}"


def artist_line(name: str, url: str) -> str:
    return f"*Artist:* [{_(name)}]({_(url)})"
