from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum

from musicbot.util import _, render_links, render_tags


class ArtistType(StrEnum):
    PERSON = 'person'
    GROUP = 'group'


class ScrobbleType(StrEnum):
    ARTIST = 'artist'
    ALBUM = 'album'
    TRACK = 'track'

    @property
    def emoji(self) -> str:
        if self == ScrobbleType.ARTIST:
            return '👩‍🎤'
        elif self == ScrobbleType.ALBUM:
            return '💿'
        elif self == ScrobbleType.TRACK:
            return '🎵'
        return ''


@dataclass
class ScrobbleSummary:
    dj: str
    """The Telegram username of the submitter."""
    chat_id: int
    """The Telegram chat ID where the scrobble request was made."""
    message_id: int | None
    """The Telegram message ID of the scrobble request message."""
    scrobble_type: ScrobbleType
    """The type of the scrobble: artist, album or track."""
    updoots: int
    """The number of updoots the scrobble has received."""
    artist_name: str
    """The artist's name."""
    artist_links: dict[str, str | None]
    """A dictionary of platform names to URLs for the artist's profiles."""
    album_title: str
    """The album's title."""
    album_links: dict[str, str | None]
    """ A dictionary of platform names to URLs for the album's profiles."""
    track_title: str
    """The track's title."""
    track_links: dict[str, str | None]
    """A dictionary of platform names to URLs for the track's profiles."""
    created_at: datetime
    """The date and time when the scrobble was created."""

    def render(self) -> str:
        short_chat_id = str(self.chat_id)[4:]
        message_link = f'https://t.me/c/{short_chat_id}/{self.message_id}' if self.message_id else None
        updoots_part = f'`🤌{str(self.updoots).ljust(3)}`'
        link_part = f'[🔗]({message_link})'
        return f'• {link_part} {updoots_part} *_{self.dj}_*: {self.scrobble_type.emoji} {_caption(self)}'


@dataclass
class Scrobble:
    id: int | None
    """A unique identifier for the scrobble."""
    dj: str
    """The Telegram username of the submitter."""
    dj_id: int
    """The Telegram user ID of the submitter."""
    chat_id: int
    """The Telegram chat ID where the scrobble request was made."""
    message_id: int | None
    """The Telegram message ID of the scrobble request message."""
    message_content: str
    """The raw text content of the scrobble request message."""
    scrobble_type: ScrobbleType
    """The type of the scrobble: artist, album or track."""
    updoots: int = 0
    """The number of updoots the scrobble has received."""
    created_at: datetime = field(default_factory=datetime.now)
    """The date when the scrobble was created."""

    artist_name: str = ''
    """The artist's name."""
    artist_genres: list[str] = field(default_factory=list)
    """A list of genres associated with the artist."""
    artist_type: ArtistType | None = ArtistType.GROUP
    """The type of the artist, e.g. 'Person' or 'Group'."""
    artist_area: str | None = None
    """The artist's area of activity."""
    artist_area_born: str | None = None
    """The artist's area of birth or formation."""
    artist_area_died: str | None = None
    """The artist's area of death or disbandment."""
    artist_born: date | None = None
    """The artist's birth year or band's formation year."""
    artist_died: date | None = None
    """The artist's death year or band's disbandment year."""
    artist_thumbnail_url: str | None = None
    """The URL of the artist's thumbnail image."""
    artist_links: dict[str, str | None] = field(default_factory=dict)
    """A dictionary of platform names to URLs for the artist's profiles."""

    album_title: str = ''
    """The album's title."""
    album_genres: list[str] = field(default_factory=list)
    """A list of tags describing the album's musical genre."""
    album_release_date: date | None = None
    """The release date of the album."""
    album_thumbnail_url: str | None = None
    """The URL of the album's thumbnail image."""
    album_links: dict[str, str | None] = field(default_factory=dict)
    """A dictionary of platform names to URLs for the album's profiles."""

    track_title: str = ''
    """The track's title."""
    track_release_date: date | None = None
    """The track's release date, if available."""
    track_duration: int = 0
    """The duration of the track in seconds."""
    track_isrc: str | None = None
    """The track's ISRC code, if available."""
    track_links: dict[str, str | None] = field(default_factory=dict)
    """A dictionary of platform names to URLs for the track's profiles."""

    def fill_field(
        self,
        field_name: str,
        value: str | int | date | list[str] | dict[str, str | None] | None = None,
    ) -> None:
        """Fill a field of the scrobble if it is not yet filled."""
        if not getattr(self, field_name):
            setattr(self, field_name, value)

    def add_artist_link(self, platform: str, url: str | None):
        self.artist_links[platform] = url

    def add_album_link(self, platform: str, url: str | None):
        self.album_links[platform] = url

    def add_track_link(self, platform: str, url: str | None):
        self.track_links[platform] = url

    def updoot(self):
        self.updoots += 1

    @property
    def search_query(self) -> str:
        return f'{self.artist_name} {self.album_title or self.track_title}'

    @property
    def links(self) -> dict[str, str]:
        return getattr(self, f'{self.scrobble_type.value}_links', {})

    @property
    def is_group(self) -> bool:
        return self.artist_type == ArtistType.GROUP

    @property
    def header(self) -> str:
        return f'{self.scrobble_type.emoji} {_caption(self)}'

    def render(self) -> str:
        parts = filter(None, [self.render_track(), self.render_album(), self.render_artist()])

        return f"""
{self.header}
\\({_(self.scrobble_type.value.capitalize())} sent by {_(self.dj)}\\)

{'\n\n'.join(parts)}
        """.strip()

    def render_track(self) -> str:
        if not self.track_title:
            return ''

        return f"""
*🎵 __Track__:* {_(self.track_title)}
*⏱️ Duration:* {self.track_duration // 60}∶{self.track_duration % 60:02d}
*🪪 ISRC:* [{_(self.track_isrc)}](https://isrcsearch.ifpi.org/?tab=code&isrcCode={self.track_isrc})
*🔗 Links:* {render_links(self.track_links)}
        """.strip()  # noqa: RUF001 - U+2236 RATIO avoids Telegram linkifying the timestamp

    def render_album(self) -> str:
        if not self.album_title:
            return ''

        return f"""
*💿 __Album__:* {_(self.album_title)}
*🏷️ Genres:* {render_tags(self.album_genres)}
*🔗 Links:* {render_links(self.album_links)}
*📅 Release Date:* {_(self.album_release_date)}
        """.strip()

    def render_artist(self) -> str:
        if self.is_group:
            born_header = '🎸 Formed in'
            died = 'Disabanded in'
            died_header = f'💔 {died}'
            age_header = '⏳ Active'
        else:
            born_header = '👶 Born in'
            died = 'Died in'
            died_header = f'💀 {died}'
            age_header = '🎂 Age'

        age_or_active = 'N/A'
        if self.artist_born and self.artist_died:
            years = self.artist_died.year - self.artist_born.year
            age_or_active = f'{years} years \\({_(self.artist_born)} — {_(self.artist_died)}\\)'
        elif self.artist_born:
            years = date.today().year - self.artist_born.year
            age_or_active = f'{years} years \\({_(self.artist_born)} — \\)'
        elif self.artist_died:
            age_or_active = f'N/A \\({died} {_(self.artist_died)}\\)'

        area_line = ''
        if self.artist_area_born and self.artist_area_died:
            area_line = f'\n*{born_header}:* {_(self.artist_area_born)} *{died_header}:* {_(self.artist_area_died)}'
        elif self.artist_area_born:
            area_line = f'\n*{born_header}:* {_(self.artist_area_born)}'
        elif self.artist_area_died:
            area_line = f'\n*{died_header}:* {_(self.artist_area_died)}'

        return f"""
*👩‍🎤 __Artist__:* {_(self.artist_name)}
*🏷️ Genres:* {render_tags(self.artist_genres)}
*{age_header}:* {age_or_active}
*📍 Area:* {_(self.artist_area)}{area_line}
*🔗 Links:* {render_links(self.artist_links)}
        """.strip()


def _caption(scrobble: Scrobble | ScrobbleSummary) -> str:
    match scrobble.scrobble_type:
        case ScrobbleType.TRACK:
            return f'{_(scrobble.artist_name)} \\- {_(scrobble.track_title)} \\({_(scrobble.album_title)}\\)'
        case ScrobbleType.ALBUM:
            return f'{_(scrobble.artist_name)} \\- {_(scrobble.album_title)}'
        case ScrobbleType.ARTIST:
            return _(scrobble.artist_name)
