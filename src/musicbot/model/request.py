from dataclasses import dataclass
from uuid import uuid4

from telegram import InlineQueryResultArticle, InputTextMessageContent

from musicbot.model.scrobble import ScrobbleType


@dataclass
class Request:
    provider_name: str
    """The name of the provider the submission was sourced from."""
    provider_id: str
    """The id of the submission in the provider's system."""
    result_type: ScrobbleType
    """The type of the search result: artist, album or track."""
    caption: str
    """A short caption describing the search result."""
    thumbnail_url: str | None
    """The URL of the search result's thumbnail image."""

    def render(self) -> InlineQueryResultArticle:
        return InlineQueryResultArticle(
            id=uuid4().hex,
            title=f'{self.result_type.emoji} {self.caption}',
            thumbnail_url=self.thumbnail_url,
            input_message_content=InputTextMessageContent(
                f'🎧 {self.provider_name}:{self.result_type}:{self.provider_id}',
            ),
        )
