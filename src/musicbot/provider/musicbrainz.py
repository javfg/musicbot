import asyncio
import re
from typing import Any

import httpx
from loguru import logger

from musicbot.config import Config
from musicbot.model.provider import ProviderRegistry, SearchableProvider
from musicbot.model.request import Request
from musicbot.model.scrobble import ArtistType, Scrobble, ScrobbleType
from musicbot.util import clean, date_from_iso

PAUSE_BETWEEN_QUERIES = 0.75


class MusicbrainzProvider(SearchableProvider):
    name = 'musicbrainz'
    weight = 40
    routes = [r'^https?://(?:www\.)?musicbrainz\.org/(release|artist)/[0-9a-f-]{32,36}$']
    amenders = []

    def __init__(
        self,
        settings: dict[str, str],
        provider_registry: ProviderRegistry,
        config: Config,
    ) -> None:
        self.client = httpx.AsyncClient(
            base_url='https://musicbrainz.org/ws/2',
            headers={'User-Agent': config.user_agent},
            timeout=config.provider_timeout,
        )

    def _get_tags(
        self,
        data: list[dict[str, str]],
    ) -> list[str]:
        tags = sorted(data, key=lambda x: x.get('count', 0), reverse=True)
        clean_tags = []
        for tag in [t for t in tags if int(t.get('count', 0)) > 0][:5]:
            if len(tag['name']) > 64:
                continue
            name = tag['name'].lower()
            clean = re.sub(r'[^a-zA-Z0-9_]', '', name.replace(' ', '_'))
            clean = re.sub(r'_+', '_', clean)
            clean_tags.append(f'#{clean}')
        unique_tags: set[str] = set(clean_tags)
        return list(unique_tags)

    async def _search(
        self,
        endpoint: str,
        query: str,
        limit: int | None = 1,
    ) -> dict[str, Any]:
        logger.debug(f'making request to {self.client.base_url}{endpoint}?{query}&fmt=json&limit={limit}')
        request = await self.client.get(
            endpoint,
            params={
                'query': query,
                'limit': limit,
                'fmt': 'json',
            },
        )
        request.raise_for_status()
        if not httpx.codes.is_success(request.status_code):
            logger.error(f'request to {endpoint} failed: {request.status_code}')
            return {}
        return request.json()

    async def _get(
        self,
        scrobble_type: ScrobbleType,
        mbid: str,
        limit: int = 1,
        inc: str = '',
    ) -> dict[str, Any]:
        scrobble_type_to_endpoint = {
            ScrobbleType.ARTIST: 'artist',
            ScrobbleType.ALBUM: 'release-group',
            ScrobbleType.TRACK: 'recording',
        }
        endpoint = scrobble_type_to_endpoint[scrobble_type]

        logger.debug(f'making request to {self.client.base_url}{endpoint}/{mbid}?fmt=json&limit={limit}&inc={inc}')
        request = await self.client.get(
            f'{endpoint}/{mbid}',
            params={
                'fmt': 'json',
                'limit': limit,
                'inc': inc,
            },
        )
        request.raise_for_status()
        if not httpx.codes.is_success(request.status_code):
            logger.error(f'request to {endpoint} failed: {request.status_code}')
            return {}
        return request.json()

    def _fill_artist(
        self,
        scrobble: Scrobble,
        data: dict[str, Any],
    ) -> Scrobble:
        scrobble.fill_field('artist_name', data['name'])
        lifespan = data.get('life-span') or {}
        if lifespan_begin := lifespan.get('begin'):
            scrobble.fill_field('artist_born', date_from_iso(lifespan_begin))
        if lifespan_end := lifespan.get('end'):
            scrobble.fill_field('artist_died', date_from_iso(lifespan_end))
        scrobble.fill_field('artist_area', (data.get('area') or {}).get('name'))
        scrobble.fill_field('artist_area_born', (data.get('begin-area') or {}).get('name'))
        scrobble.fill_field('artist_area_died', (data.get('end-area') or {}).get('name'))
        scrobble.fill_field('artist_genres', self._get_tags(data.get('tags', [])))
        scrobble.add_artist_link('musicbrainz', f'https://musicbrainz.org/artist/{data["id"]}')
        artist_type = data.get('type')
        logger.debug(f'artist type from musicbrainz: {artist_type}')
        if artist_type:
            try:
                scrobble.fill_field('artist_type', ArtistType(artist_type.lower()))
            except ValueError:
                logger.warning(f'unknown artist type from musicbrainz: {artist_type}')
        return scrobble

    async def _fill_album(
        self,
        scrobble: Scrobble,
        data: dict[str, Any],
    ) -> Scrobble:
        scrobble.fill_field('album_title', data['title'])
        scrobble.fill_field('album_release_date', date_from_iso(data.get('first-release-date')))
        scrobble.add_album_link('musicbrainz', f'https://musicbrainz.org/release-group/{data["id"]}')
        scrobble.fill_field('album_genres', self._get_tags(data.get('tags', [])))

        artist_mbid = data.get('artist-credit', [{}])[0].get('artist', {}).get('id')
        if artist_mbid:
            await asyncio.sleep(PAUSE_BETWEEN_QUERIES)
            artist_data = await self._get(ScrobbleType.ARTIST, artist_mbid, limit=1, inc='tags')
            return self._fill_artist(scrobble, artist_data)
        return scrobble

    async def _fill_track(
        self,
        scrobble: Scrobble,
        data: dict[str, Any],
    ) -> Scrobble:
        scrobble.fill_field('track_title', data['title'])
        scrobble.fill_field('track_duration', data.get('length', 0) // 1000)
        scrobble.fill_field('track_release_date', date_from_iso(data.get('first-release-date')))
        scrobble.fill_field('track_isrc', data.get('isrcs', [None])[0])
        scrobble.add_track_link('musicbrainz', f'https://musicbrainz.org/recording/{data["id"]}')

        release_group_mbid = data.get('releases', [{}])[0].get('release-group', {}).get('id')
        if release_group_mbid:
            await asyncio.sleep(PAUSE_BETWEEN_QUERIES)
            release_data = await self._get(ScrobbleType.ALBUM, release_group_mbid, limit=1, inc='tags+artist-credits')
            return await self._fill_album(scrobble, release_data)
        return scrobble

    async def search(self, query: str, limit: int | None = 25) -> list[Request]:
        query = query.strip().replace(' ', ' AND ')
        logger.debug(f'searching for query "{query}" in Musicbrainz')
        artists_request = await self._search('/artist', f'{query}', limit=limit)
        artists = artists_request.get('artists', [])
        await asyncio.sleep(PAUSE_BETWEEN_QUERIES)
        release_groups_request = await self._search('/release-group', f'{query}', limit=limit)
        release_groups = release_groups_request.get('release-groups', [])
        await asyncio.sleep(PAUSE_BETWEEN_QUERIES)
        recordings_request = await self._search('/recording', f'{query}', limit=limit)
        recordings = recordings_request.get('recordings', [])

        results = []

        logger.debug(f'got {len(artists)} artists')
        for artist in artists:
            caption = artist['name']
            request = Request(
                provider_name=self.name,
                provider_id=artist['id'],
                result_type=ScrobbleType.ARTIST,
                caption=caption,
                thumbnail_url=None,
            )
            results.append(request)

        logger.debug(f'got {len(release_groups)} release groups')
        for release_group in release_groups:
            artist_name = release_group['artist-credit'][0]['artist']['name']
            caption = f'{artist_name} - {release_group["title"]}'
            request = Request(
                provider_name=self.name,
                provider_id=release_group['id'],
                result_type=ScrobbleType.ALBUM,
                caption=caption,
                thumbnail_url=None,
            )
            results.append(request)
        logger.debug(f'got {len(recordings)} recordings')
        for recording in recordings:
            artist_name = recording['artist-credit'][0]['artist']['name']
            album_title = recording['releases'][0]['title'] if recording.get('releases') else ''
            caption = f'{recording["artist-credit"][0]["artist"]["name"]} - {recording["title"]}'
            if album_title:
                caption += f' ({album_title})'
            request = Request(
                provider_name=self.name,
                provider_id=recording['id'],
                result_type=ScrobbleType.TRACK,
                caption=caption,
                thumbnail_url=None,
            )
            results.append(request)
        logger.info(f'musicbrainz search "{query}": {len(results)} results')
        return results

    async def fill(
        self,
        scrobble: Scrobble,
        provider_id: str | None,
    ) -> Scrobble:
        match scrobble.scrobble_type:
            case ScrobbleType.ARTIST:
                if provider_id:
                    artist_data = await self._get(scrobble.scrobble_type, provider_id, inc='tags')
                    scrobble = self._fill_artist(scrobble, artist_data)
                    logger.debug(f'filled artist data from musicbrainz for artist: {scrobble.artist_name}')
                else:
                    logger.debug(f'searching for artist with query: {scrobble.artist_name}')
                    artist_data = await self._search('artist', f'artist:{scrobble.artist_name}', limit=25)
                    artists = artist_data.get('artists', [])
                    if not artists:
                        logger.debug('no artists found')
                        return scrobble
                    artist_index = 0
                    for index, artist in enumerate(artists):
                        if clean(artist['name']) == clean(scrobble.artist_name):
                            logger.debug(f'found good match artist with mbid: {artist["id"]}')
                            artist_index = index
                            break
                    scrobble = self._fill_artist(scrobble, artist_data['artists'][artist_index])
                    logger.info(f'filled artist {scrobble.artist_name}')
                return scrobble

            case ScrobbleType.ALBUM:
                if provider_id:
                    release_data = await self._get(scrobble.scrobble_type, provider_id, inc='artists+releases+tags')
                    scrobble = await self._fill_album(scrobble, release_data)
                else:
                    year = f' AND date:{scrobble.album_release_date.year}' if scrobble.album_release_date else ''
                    query = f'artist:{scrobble.artist_name} AND release_group:{scrobble.album_title}{year}'
                    logger.debug(f'searching for release with query: {query}')
                    release_data = await self._search('release', query, limit=25)
                    releases = release_data.get('releases', [])
                    if not releases:
                        logger.debug(f'no releases found, try again excluding year: {query}')
                        query = f'artist:{scrobble.artist_name} AND release_group:{scrobble.album_title}'
                        release_data = await self._search('release', query, limit=25)
                        releases = release_data.get('releases', [])
                        if not releases:
                            logger.debug('no releases found')
                            return scrobble
                    release_index = 0
                    for index, release in enumerate(releases):
                        if clean(release['title']) == clean(scrobble.album_title):
                            logger.debug(f'found good match release with mbid: {release["id"]}')
                            release_index = index
                            break
                    release_group_data = await self._get(
                        ScrobbleType.ALBUM,
                        releases[release_index]['release-group']['id'],
                        inc='tags+artist-credits',
                    )
                    scrobble = await self._fill_album(scrobble, release_group_data)
                    logger.info(f'filled album data from musicbrainz for album: {scrobble.album_title}')
                return scrobble

            case ScrobbleType.TRACK:
                if provider_id:
                    recording_data = await self._get(
                        scrobble.scrobble_type,
                        provider_id,
                        inc='artists+release-groups+releases',
                    )
                    scrobble = await self._fill_track(scrobble, recording_data)
                else:
                    an = f'artist:{scrobble.artist_name}' if scrobble.artist_name else ''
                    at = f'release_group:{scrobble.album_title}' if scrobble.album_title else ''
                    tt = f'recording:{scrobble.track_title}' if scrobble.track_title else ''
                    query = ' AND '.join(filter(None, [an, at, tt]))
                    logger.debug(f'searching for recording with query: {query}')
                    recording_data = await self._search('recording', query, limit=25)
                    recordings = recording_data.get('recordings', [])
                    if not recordings:
                        logger.debug('no recordings found')
                        return scrobble
                    recording_index = 0
                    for index, recording in enumerate(recordings):
                        if clean(recording['title']) == clean(scrobble.track_title):
                            logger.debug(f'found good match recording with mbid: {recording["id"]}')
                            recording_index = index
                            break
                    scrobble = await self._fill_track(scrobble, recording_data['recordings'][recording_index])
                    logger.info(f'filled track data from musicbrainz for track: {scrobble.track_title}')
                return scrobble
