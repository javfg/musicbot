import re

import httpx
from cache import AsyncTTL
from loguru import logger
from spotify_sdk import AsyncSpotifyClient
from spotify_sdk.auth import AsyncClientCredentials
from spotify_sdk.models import Album, Artist, SimplifiedAlbum, SimplifiedArtist, Track

from musicbot.config import PROVIDER_CACHE_SIZE, PROVIDER_CACHE_TTL, Config
from musicbot.model.provider import Amender, Provider, SearchableProvider
from musicbot.model.request import Request
from musicbot.model.scrobble import Scrobble, ScrobbleType
from musicbot.util.date import date_from_iso

FAKE_USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64; rv:155.0) Gecko/20100101 Firefox/155.0'


class SpotifyProvider(SearchableProvider):
    name = 'spotify'
    weight = 30
    routes = [
        r'https?://open\.spotify\.com/(?:intl-[a-z]+/)?(?P<type>track|album|artist)/(?P<id>[\w]+)',
        r'https?://open\.spotify\.com/s/(?P<id>[\w]+)',
    ]
    amenders = [
        Amender(
            pattern=r'https?://open\.spotify\.com/(?:intl-[a-z]+/)?track/(?P<id>[\w]+)',
            link_type=ScrobbleType.TRACK,
            link_key='spotify',
        ),
        Amender(
            pattern=r'https?://open\.spotify\.com/(?:intl-[a-z]+/)?album/(?P<id>[\w]+)',
            link_type=ScrobbleType.ALBUM,
            link_key='spotify',
        ),
        Amender(
            pattern=r'https?://open\.spotify\.com/(?:intl-[a-z]+/)?artist/(?P<id>[\w]+)',
            link_type=ScrobbleType.ARTIST,
            link_key='spotify',
        ),
    ]

    def __init__(self, settings: dict[str, str], provider_registry: list[Provider], config: Config) -> None:
        auth = AsyncClientCredentials(
            client_id=settings['spotify_client_id'],
            client_secret=settings['spotify_client_secret'],
        )
        self.client = AsyncSpotifyClient(auth_provider=auth)
        self.http_client = httpx.AsyncClient(
            headers={'User-Agent': FAKE_USER_AGENT},
            timeout=config.provider_timeout,
        )

    @AsyncTTL(maxsize=PROVIDER_CACHE_SIZE, time_to_live=PROVIDER_CACHE_TTL)
    async def _get(self, id: str, scrobble_type: ScrobbleType) -> Album | Artist | Track:
        match scrobble_type:
            case ScrobbleType.ARTIST:
                return await self.client.artists.get(id)
            case ScrobbleType.ALBUM:
                return await self.client.albums.get(id)
            case ScrobbleType.TRACK:
                return await self.client.tracks.get(id)

    def _caption(self, content: Album | Artist | Track | SimplifiedAlbum) -> str:
        match content:
            case Artist():
                return content.name
            case Album() | SimplifiedAlbum():
                return f'{content.artists[0].name} - {content.name}'
            case Track():
                return f'{content.artists[0].name} - {content.name}'

    def _request_type(self, content: Album | Artist | Track | SimplifiedAlbum | SimplifiedArtist) -> ScrobbleType:
        match content:
            case Artist() | SimplifiedArtist():
                return ScrobbleType.ARTIST
            case Album() | SimplifiedAlbum():
                return ScrobbleType.ALBUM
            case Track():
                return ScrobbleType.TRACK

    def _get_image_url(self, obj: object, index: int = 0) -> str | None:
        images = getattr(obj, 'images', None)
        if not isinstance(images, list) or len(images) <= index:
            return None
        return getattr(images[index], 'url', None)

    async def _resolve_short_link(self, url: str) -> str:
        resp = await self.http_client.get(url, follow_redirects=True)
        resp.raise_for_status()
        logger.debug(f'{resp.url} {resp.headers}')
        return str(resp.url)

    async def search(self, query: str, limit: int | None = 5) -> list[Request]:
        # if it is a shortened link, we need to resolve it
        if re.match(self.routes[1], query):
            query = await self._resolve_short_link(query)
            logger.debug(f'spotify shortened resolves to: {query}')

        # first we try to match the query to a spotify link
        results = []
        m = re.match(self.routes[0], query)

        # if match, use the id to get the resource from spotify directly
        if m:
            request_type = ScrobbleType(m.group('type'))
            request_id = m.group('id')
            logger.debug(f'extracted spotify id: {request_id} and type: {request_type}')
            results = [await self._get(request_id, request_type)]
        # otherwise, search spotify and get some results
        else:
            logger.debug(f'searching spotify for query: {query}')
            limit = limit or 5
            data = await self.client.search.search(
                q=query,
                types=['artist', 'album', 'track'],
                limit=limit,
            )
            results = [
                *(data.artists.items if data.artists else []),
                *(data.albums.items if data.albums else []),
                *(data.tracks.items if data.tracks else []),
            ]

        # build requests with those results and return them
        requests = []
        for result in results:
            request_id = result.id
            request_type = self._request_type(result)
            request = Request(
                provider_name=self.name,
                provider_id=request_id,
                result_type=request_type,
                caption=self._caption(result),
                thumbnail_url=result.images[0].url
                if isinstance(result, (Artist, Album, SimplifiedAlbum)) and result.images
                else None,
            )
            requests.append(request)
        logger.debug(f'spotify search with id: {request_id} and type: {request_type}')
        return requests

    def _fill_artist(self, scrobble: Scrobble, artist: Artist) -> Scrobble:
        scrobble.fill_field('artist_name', artist.name)
        scrobble.fill_field('artist_thumbnail_url', self._get_image_url(artist))
        scrobble.add_artist_link('spotify', artist.external_urls.spotify)
        return scrobble

    def _fill_album(self, scrobble: Scrobble, album: Album) -> Scrobble:
        scrobble.fill_field('album_title', album.name)
        scrobble.fill_field('album_release_date', date_from_iso(album.release_date))
        scrobble.fill_field('album_thumbnail_url', self._get_image_url(album))
        scrobble.add_album_link('spotify', album.external_urls.spotify)
        return scrobble

    def _fill_track(self, scrobble: Scrobble, track: Track) -> Scrobble:
        scrobble.fill_field('track_title', track.name)
        scrobble.fill_field('track_release_date', track.album.release_date)
        scrobble.fill_field('track_duration', track.duration_ms // 1000)
        scrobble.fill_field('track_isrc', track.external_ids.isrc)
        scrobble.add_track_link('spotify', track.external_urls.spotify)
        return scrobble

    def _match(self, scrobble: Scrobble, results: list[Artist | Album | Track]) -> Artist | Album | Track:
        match scrobble.scrobble_type:
            case ScrobbleType.ARTIST:
                for result in results:
                    if result.name.lower() == scrobble.artist_name.lower():
                        return result
            case ScrobbleType.ALBUM:
                for result in results:
                    if result.name.lower() == scrobble.album_title.lower():
                        return result
            case ScrobbleType.TRACK:
                for result in results:
                    if result.name.lower() == scrobble.track_title.lower():
                        return result
        return results[0]

    async def fill(self, scrobble: Scrobble, provider_id: str | None) -> Scrobble:
        # if there is no provider id, try to search
        result: Album | Artist | Track
        if not provider_id:
            an = scrobble.artist_name.replace(' ', '+')
            at = scrobble.album_title.replace(' ', '+')
            tt = scrobble.track_title.replace(' ', '+')
            match scrobble.scrobble_type:
                case ScrobbleType.ARTIST:
                    q = f'artist:"{an}"'
                case ScrobbleType.ALBUM:
                    q = f'artist:"{an}" album:"{at}"'
                case ScrobbleType.TRACK:
                    q = f'artist:"{an}" track:"{tt}"'

            logger.debug(f'searching spotify for query: "{q}" type {scrobble.scrobble_type.value}')
            data = await self.client.search.search(q=q, types=[scrobble.scrobble_type.value], limit=25)
            results = getattr(data, scrobble.scrobble_type.value + 's')
            if not results or not results.items:
                logger.debug(f'no spotify results found for query: {q}')
                return scrobble
            provider_id = self._match(scrobble, results.items).id
            logger.debug(f'found spotify provider id for query {q}: {provider_id}')
        result = await self._get(provider_id, scrobble.scrobble_type)

        if not isinstance(result, Artist):
            # the SimplifiedArtist inside track/album does not include images
            result_artist = await self._get(result.artists[0].id, ScrobbleType.ARTIST)
            scrobble = self._fill_artist(scrobble, result_artist)

        # then we fill the scrobble (except artist in the case of track/album, which we filled above)
        if isinstance(result, Track):
            scrobble = self._fill_track(scrobble, result)
            scrobble = self._fill_album(scrobble, result.album)
        elif isinstance(result, (Album, SimplifiedAlbum)):
            scrobble = self._fill_album(scrobble, result)
        elif isinstance(result, (Artist, SimplifiedArtist)):
            scrobble = self._fill_artist(scrobble, result)

        return scrobble
