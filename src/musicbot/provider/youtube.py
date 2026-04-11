import yt_dlp
from loguru import logger

from musicbot.config import Config
from musicbot.model.provider import Amender, ProviderRegistry, SearchableProvider
from musicbot.model.request import Request
from musicbot.model.scrobble import Scrobble, ScrobbleType
from musicbot.util import clean


class YoutubeProvider(SearchableProvider):
    name = 'youtube'
    weight = 10
    routes = [r'https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)[\w-]+']
    amenders = [
        Amender(
            r'https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)[\w-]+',
            ScrobbleType.TRACK,
            'youtube',
        )
    ]

    def __init__(
        self,
        settings: dict[str, str],
        provider_registry: ProviderRegistry,
        config: Config,
    ) -> None:
        fill_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }
        self.fill_client = yt_dlp.YoutubeDL(fill_opts)

        search_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }
        self.search_client = yt_dlp.YoutubeDL(search_opts)
        self.provider_registry = provider_registry

    async def search(self, query: str, limit: int | None = None) -> list[Request]:
        # youtube search will be used when pasting a youtube link in the bot request

        # first get the video title from that link
        info = self.fill_client.extract_info(query, download=False)
        title = clean(info['title'])
        logger.debug(f'found youtube video title: {title}')

        # but youtube is unreliable as a source, so use search provider chain
        results = []
        for sp in self.provider_registry.search_providers:
            results = await sp.search(title)
            if results:
                break
        return results

    async def fill(self, scrobble: Scrobble, provider_id: str | None) -> Scrobble:
        # youtube only fills track scrobbles
        if scrobble.scrobble_type is not ScrobbleType.TRACK:
            return scrobble

        # search for the track on youtube and get the video link
        q = ' - '.join([scrobble.artist_name, scrobble.album_title, scrobble.track_title])
        results = self.fill_client.extract_info(f'ytsearch1:{q}', download=False)
        if not results or not results['entries']:
            return scrobble
        link = f'https://www.youtube.com/watch?v={results["entries"][0]["id"]}'
        scrobble.track_links['youtube'] = link
        logger.debug(f'found youtube link: {link}')

        return scrobble
