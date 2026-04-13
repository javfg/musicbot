import httpx
from loguru import logger

from musicbot.config import Config
from musicbot.model.provider import ProviderRegistry, SearchableProvider
from musicbot.model.request import Request
from musicbot.model.scrobble import Scrobble, ScrobbleType
from musicbot.util.date import date_from_iso


class DeezerProvider(SearchableProvider):
    name = 'deezer'
    weight = 50
    routes = [r'https?://(?:www\.)?(?:deezer\.com/)(track|album|artist)/\d+']
    amenders = []

    def __init__(
        self,
        settings: dict,
        provider_registry: ProviderRegistry,
        config: Config,
    ) -> None:
        self.client = httpx.AsyncClient(
            base_url='https://api.deezer.com',
            headers={'User-Agent': config.user_agent},
            timeout=config.provider_timeout,
        )

    async def search(self, query: str, limit: int | None = 15) -> list[Request]:
        request = await self.client.get('/search', params={'q': query, 'limit': limit})
        request.raise_for_status()
        if not httpx.codes.is_success(request.status_code):
            logger.error(f'deezer search request failed: {request.status_code}')
            return []
        data = request.json().get('data', [])

        ids = set()
        results = []

        # deezer returns only tracks on the search endpoint, but those include
        # album and artist data, so we can generate three results per entry

        for datum in data:
            artist_request = Request(
                provider_name=self.name,
                provider_id=datum['artist']['id'],
                result_type=ScrobbleType.ARTIST,
                caption=datum['artist']['name'],
                thumbnail_url=datum['artist'].get('picture'),
            )
            album_request = Request(
                provider_name=self.name,
                provider_id=datum['album']['id'],
                result_type=ScrobbleType.ALBUM,
                caption=f'{datum["artist"]["name"]} - {datum["album"]["title"]}',
                thumbnail_url=datum['album'].get('cover'),
            )
            track_request = Request(
                provider_name=self.name,
                provider_id=datum['id'],
                result_type=ScrobbleType.TRACK,
                caption=f'{datum["artist"]["name"]} - {datum["title"]}',
                thumbnail_url=datum.get('album', {}).get('cover'),
            )
            for item in (artist_request, album_request, track_request):
                if item.provider_id not in ids:
                    results.append(item)
                    ids.add(item.provider_id)

        logger.info(f'deezer search "{query}": {len(results)} results')
        return results

    def _fill_artist(self, scrobble: Scrobble, data: dict) -> Scrobble:
        scrobble.fill_field('artist_name', data['name'])
        scrobble.fill_field('artist_thumbnail_url', data.get('picture'))
        scrobble.add_artist_link('deezer', 'https://www.deezer.com/artist/' + str(data['id']))
        return scrobble

    def _fill_album(self, scrobble: Scrobble, data: dict) -> Scrobble:
        scrobble.fill_field('album_title', data['title'])
        scrobble.fill_field('album_release_date', date_from_iso(data.get('release_date')))
        scrobble.fill_field('album_thumbnail_url', data.get('cover'))
        scrobble.add_album_link('deezer', 'https://www.deezer.com/album/' + str(data['id']))
        return self._fill_artist(scrobble, data['artist'])

    def _fill_track(self, scrobble: Scrobble, data: dict) -> Scrobble:
        scrobble.fill_field('track_title', data['title'])
        scrobble.fill_field('track_duration', data.get('duration', 0))
        scrobble.fill_field('track_release_date', date_from_iso(data.get('release_date')))
        scrobble.fill_field('track_isrc', data.get('isrc'))
        scrobble.add_track_link('deezer', 'https://www.deezer.com/track/' + str(data['id']))
        data['album']['artist'] = data['artist']  # ensure album has artist inside
        scrobble = self._fill_album(scrobble, data['album'])
        return self._fill_artist(scrobble, data['artist'])

    async def fill(self, scrobble: Scrobble, provider_id: str | None) -> Scrobble:
        # if there is no provider id, try to search
        if not provider_id:
            results = await self.search(query=scrobble.search_query, limit=25)
            if not results:
                logger.debug(f'no results found for query: {scrobble.search_query}')
                return scrobble
            filtered = list(filter(lambda r: r.result_type == scrobble.scrobble_type, results))
            if not filtered:
                logger.debug(f'no results found for query: {scrobble.search_query}')
                return scrobble
            provider_id = filtered[0].provider_id
            for result in filtered:
                match scrobble.scrobble_type:
                    case ScrobbleType.ARTIST:
                        if result.caption.lower() == scrobble.artist_name.lower():
                            provider_id = result.provider_id
                            break
                    case ScrobbleType.ALBUM:
                        if result.caption.lower() == f'{scrobble.artist_name.lower()} - {scrobble.album_title.lower()}':
                            provider_id = result.provider_id
                            break
                    case ScrobbleType.TRACK:
                        if result.caption.lower() == f'{scrobble.artist_name.lower()} - {scrobble.track_title.lower()}':
                            provider_id = result.provider_id
                            break
            logger.debug(f'found provider id {provider_id} for query: {scrobble.search_query}')

        # get the content
        request_url = f'/{scrobble.scrobble_type!s}/{provider_id}'
        request = await self.client.get(request_url, params={'inc': 'artist,album'})
        request.raise_for_status()
        if not httpx.codes.is_success(request.status_code):
            logger.error(f'deezer content request failed: {request.status_code}')
            return scrobble
        data = request.json()
        logger.debug(f'got data from deezer for provider id {provider_id}')

        # fill the scrobble with the data
        match scrobble.scrobble_type:
            case ScrobbleType.ARTIST:
                return self._fill_artist(scrobble, data)
            case ScrobbleType.ALBUM:
                return self._fill_album(scrobble, data)
            case ScrobbleType.TRACK:
                return self._fill_track(scrobble, data)
        logger.debug(f'filled {scrobble.scrobble_type!s} scrobble with data for provider id {provider_id}')
