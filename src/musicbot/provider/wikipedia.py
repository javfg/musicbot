import httpx
from curl_cffi.requests import AsyncSession
from loguru import logger

from musicbot.config import Config
from musicbot.model.provider import Amender, Provider, ProviderRegistry
from musicbot.model.scrobble import Scrobble, ScrobbleType


class WikipediaProvider(Provider):
    name = 'wikipedia'
    weight = 10
    routes = [r'^https?://(\w{2,3})\.wikipedia\.org/wiki/([\w%\-]+)']
    amenders = [
        Amender(
            pattern=r'https?://(\w{2,3})\.wikipedia\.org/wiki/[^\s\]]+',
            link_type=ScrobbleType.ARTIST,
            link_key='wikipedia',
        )
    ]

    def __init__(
        self,
        settings: dict[str, str],
        provider_registry: ProviderRegistry,
        config: Config,
    ) -> None:
        pass

    async def fill(self, scrobble: Scrobble, provider_id: str | None) -> Scrobble:
        # wikipedia fills the artist's wikipedia link only
        q = scrobble.artist_name
        request_url = 'https://en.wikipedia.org/w/rest.php/v1/search/page'
        async with AsyncSession(impersonate='chrome120') as session:
            request = await session.get(request_url, params={'q': q, 'limit': 1})
            request.raise_for_status()
            if not httpx.codes.is_success(request.status_code):
                logger.error(f'wikipedia search request failed: {request.status_code}')
                return scrobble
        data = request.json()
        pages = data.get('pages')
        if pages:
            result = pages[0].get('key')
            if result:
                link = f'https://en.wikipedia.org/wiki/{result}'
                scrobble.artist_links['wikipedia'] = link
                logger.debug(f'found wikipedia link: {link}')

        return scrobble
