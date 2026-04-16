import httpx
from loguru import logger

from musicbot.config import Config
from musicbot.model.provider import Amender, Provider, ProviderRegistry
from musicbot.model.scrobble import Scrobble, ScrobbleType


class GeniusProvider(Provider):
    name = 'genius'
    weight = 10
    routes = []
    amenders = [
        Amender(
            pattern=r'https?://genius\.com/[\w\-]+-lyrics',
            link_type=ScrobbleType.TRACK,
            link_key='lyrics',
        )
    ]

    def __init__(
        self,
        settings: dict[str, str],
        provider_registry: ProviderRegistry,
        config: Config,
    ) -> None:
        access_token = config.extra.get('genius_access_token')
        authorization = f'Bearer {access_token}'

        self.client = httpx.AsyncClient(
            base_url='https://api.genius.com',
            headers={
                'User-Agent': config.user_agent,
                'Authorization': authorization,
            },
            timeout=config.provider_timeout,
        )

    async def fill(self, scrobble: Scrobble, provider_id: str | None) -> Scrobble:
        # genius fills the lyrics of tracks only
        if scrobble.scrobble_type != ScrobbleType.TRACK:
            return scrobble

        q = f'{scrobble.artist_name} {scrobble.track_title}'
        try:
            response = await self.client.get('search', params={'q': q})
            response.raise_for_status()
        except httpx.HTTPError as e:
            logger.error(f'genius search request failed: {e}')
            return scrobble

        data = response.json()
        hits = data.get('response', {}).get('hits', [])
        if hits:
            lyrics_path = hits[0].get('result', {}).get('path')
            if lyrics_path:
                link = f'https://genius.com{lyrics_path}'
                scrobble.artist_links['lyrics'] = link
                logger.debug(f'found genius lyrics link: {link}')

        return scrobble
