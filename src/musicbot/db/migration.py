import json
from datetime import datetime

import aiosqlite
from loguru import logger

from musicbot.config import Config
from musicbot.db.operations import save_scrobble
from musicbot.db.store import StoreRegistry
from musicbot.model.scrobble import Scrobble, ScrobbleType

OLD_DB = 'old_db.json'  # the path to your old db
CHAT_ID = -1  # the chat_id of the group to migrate
DJ_IDS = {
    # your old djs, for example:
    # 'DJ Name': 123456789,
}


def parse_date(value: str | None) -> datetime:
    if not value:
        return datetime.fromtimestamp(0)
    value = value.removeprefix('{datetimeserializer}:')
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return datetime.fromtimestamp(0)


def parse_scrobble_type(value: str | None) -> ScrobbleType:
    if not value:
        return ScrobbleType.TRACK
    value = value.removeprefix('{submissiontypeserializer}:')
    return ScrobbleType(value)


async def load_entry(entry: dict[str, str], conn: aiosqlite.Connection, config: Config) -> None:
    dj = entry.get('dj', '')
    genres = entry.get('artist_genre_tags', [])
    s = Scrobble(
        id=None,
        dj=dj,
        dj_id=DJ_IDS.get(dj, -1),
        chat_id=CHAT_ID,
        message_id=-1,
        message_content='',
        scrobble_type=parse_scrobble_type(entry.get('submission_type')),
        created_at=parse_date(entry.get('submission_date')),
        artist_name=entry.get('artist_name', ''),
        artist_genres=[g.lstrip('#') for g in genres],
        artist_links={'spotify': entry.get('artist_url')},
        album_title=entry.get('album_name', ''),
        album_release_date=parse_date(entry.get('album_release_date')),
        album_links={'spotify': entry.get('album_url')},
        track_title=entry.get('track_name', ''),
        track_links={
            'spotify': entry.get('track_url'),
            'youtube': entry.get('track_url_youtube'),
        },
    )
    scrobble_id = await save_scrobble(conn, s)
    logger.info(f'scrobble saved successfully with id: {scrobble_id}')


async def migrate(config: Config) -> None:
    store_registry = StoreRegistry.create(config)
    store = await store_registry.get(CHAT_ID)

    with open(OLD_DB) as f:
        async with store.transaction() as conn:
            data = json.load(f)
            entries = data.get('_default', {})
            for e in entries.values():
                await load_entry(e, conn, config)
    await store.close()
