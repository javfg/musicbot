import json
from datetime import datetime

import aiosqlite
from loguru import logger

from musicbot.model.scrobble import Scrobble, ScrobbleSummary, ScrobbleType
from musicbot.model.stats import UserStats


async def save_scrobble(
    conn: aiosqlite.Connection,
    scrobble: Scrobble,
) -> int:
    async with conn.execute(
        """
        INSERT INTO scrobbles (
            dj, dj_id, chat_id, message_id, message_content, scrobble_type,
            artist_name, artist_type, artist_area, artist_area_born, artist_area_died,
            artist_born, artist_died, artist_thumbnail_url, artist_links,
            album_title, album_release_date, album_thumbnail_url, album_links,
            track_title, track_release_date, track_duration, track_isrc, track_links,
            created_at
        ) VALUES (
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?
        )
        """,
        (
            scrobble.dj,
            scrobble.dj_id,
            scrobble.chat_id,
            scrobble.message_id,
            scrobble.message_content,
            scrobble.scrobble_type,
            scrobble.artist_name,
            scrobble.artist_type,
            scrobble.artist_area,
            scrobble.artist_area_born,
            scrobble.artist_area_died,
            scrobble.artist_born,
            scrobble.artist_died,
            scrobble.artist_thumbnail_url,
            json.dumps(scrobble.artist_links),
            scrobble.album_title,
            scrobble.album_release_date,
            scrobble.album_thumbnail_url,
            json.dumps(scrobble.album_links),
            scrobble.track_title,
            scrobble.track_release_date,
            scrobble.track_duration,
            scrobble.track_isrc,
            json.dumps(scrobble.track_links),
            scrobble.created_at,
        ),
    ) as cursor:
        scrobble_id = cursor.lastrowid

    if scrobble_id is None:
        raise Exception('failed to insert scrobble into database')

    # INJECTION RISK, rule for interpolation is disabled in the next queries
    genres = [*scrobble.artist_genres, *scrobble.album_genres]
    if genres:
        await conn.execute(
            'INSERT OR IGNORE INTO tags (name) VALUES ' + ','.join('(?)' for _ in genres),  # noqa: S608
            genres,
        )
    if scrobble.artist_genres:
        await conn.execute(
            'INSERT OR IGNORE INTO artist_tags (scrobble_id, tag_id, dj_id) '  # noqa: S608
            'SELECT ?, id, ? FROM tags WHERE name IN (' + ','.join('?' for _ in scrobble.artist_genres) + ')',
            [scrobble_id, scrobble.dj_id, *scrobble.artist_genres],
        )
    if scrobble.album_genres:
        await conn.execute(
            'INSERT OR IGNORE INTO album_tags (scrobble_id, tag_id) '  # noqa: S608
            'SELECT ?, id FROM tags WHERE name IN (' + ','.join('?' for _ in scrobble.album_genres) + ')',
            [scrobble_id, *scrobble.album_genres],
        )

    return scrobble_id


async def updoot_scrobble(
    conn: aiosqlite.Connection,
    scrobble_id: int,
    user_id: int,
) -> tuple[bool, int]:
    cursor = await conn.execute(
        'INSERT OR IGNORE INTO updoots (scrobble_id, user_id) VALUES (?, ?)',
        (scrobble_id, user_id),
    )
    inserted = cursor.rowcount > 0
    if inserted:
        async with conn.execute(
            'UPDATE scrobbles SET updoots = updoots + 1 WHERE id = ? RETURNING updoots',
            (scrobble_id,),
        ) as cursor:
            row = await cursor.fetchone()
            if row is None or not row[0]:
                raise Exception('failed to fetch updoot count for scrobble_id: ' + str(scrobble_id))
            return True, row[0]
    return False, -1


async def update_scrobble_links(
    conn: aiosqlite.Connection,
    message_id: int,
    amender_user_id: int,
    which_links: ScrobbleType,
    link_key: str,
    new_link_value: str,
) -> tuple[str, str]:
    """Update scrobble links in the database, return the old and new link values."""
    links_dict_name = f'{which_links.value}_links'

    logger.debug(
        f'updating scrobble link {which_links}.{link_key}={new_link_value} for '
        f'message_id {message_id}, amender_user_id {amender_user_id}, '
    )

    async with conn.execute(
        # INJECTION RISK, rule for interpolation is disabled in the next query
        f'SELECT id, dj_id, {links_dict_name} FROM scrobbles WHERE message_id = ?',  # noqa: S608
        (message_id,),
    ) as cursor:
        row = await cursor.fetchone()

    if row is None:
        raise Exception('scrobble not found for message_id: ' + str(message_id))

    scrobble_id, dj_id, links_json = row

    if dj_id != amender_user_id:
        raise PermissionError('only the original submitter can amend the scrobble links')

    links = json.loads(links_json) if links_json else {}
    old_link_value = links.get(link_key, '')
    links[link_key] = new_link_value
    new_links_json = json.dumps(links)

    # INJECTION RISK, rule for interpolation is disabled in the next query
    await conn.execute(
        f'UPDATE scrobbles SET {links_dict_name} = ? WHERE id = ?',  # noqa: S608
        (new_links_json, scrobble_id),
    )

    return old_link_value, new_link_value


async def get_ranking(
    conn: aiosqlite.Connection,
    chat_id: int,
    after: datetime = datetime.min,
    before: datetime = datetime.max,
    max_results: int = 10,
) -> dict[str, int]:
    query = """
        SELECT dj, COUNT(*) FROM scrobbles
        WHERE chat_id = ?
        AND created_at >= ?
        AND created_at <= ?
        GROUP BY dj ORDER BY COUNT(*) DESC LIMIT ?
    """
    params = [chat_id, after, before, max_results]
    async with conn.execute(query, params) as cursor:
        return {row[0]: row[1] async for row in cursor}


async def get_user_stats(
    conn: aiosqlite.Connection,
    dj_id: int,
    chat_id: int,
) -> UserStats:
    query_scrobble_count = 'SELECT COUNT(*) FROM scrobbles WHERE chat_id = ? AND dj_id = ?'
    params: list = [chat_id, dj_id]
    async with conn.execute(query_scrobble_count, params) as cursor:
        scrobble_count_row = await cursor.fetchone()
        scrobble_count = scrobble_count_row[0] if scrobble_count_row else 0

    query_fav_tags = """
        SELECT t.name, COUNT(*) as count
        FROM artist_tags at
        JOIN tags t ON t.id = at.tag_id
        WHERE at.dj_id = ?
        GROUP BY at.tag_id
        ORDER BY count DESC
        LIMIT 5
    """
    async with conn.execute(query_fav_tags, (dj_id,)) as cursor:
        fav_tags = {row[0]: row[1] async for row in cursor}

    query_different_tags = 'SELECT COUNT(DISTINCT tag_id) FROM artist_tags WHERE dj_id = ?'
    async with conn.execute(query_different_tags, (dj_id,)) as cursor:
        different_tags_row = await cursor.fetchone()
        different_tags = different_tags_row[0] if different_tags_row else 0

    return UserStats(
        scrobbles=scrobble_count,
        fav_tags=list(fav_tags.items()),
        different_tags=different_tags,
    )


async def get_scrobble_summaries(
    conn: aiosqlite.Connection,
    chat_id: int,
    after: datetime | None = datetime.min,
    before: datetime | None = datetime.max,
) -> list[ScrobbleSummary]:
    query = """
        SELECT
            dj, chat_id, message_id,
            scrobble_type, updoots,
            artist_name, artist_links,
            album_title, album_links,
            track_title, track_links,
            created_at
        FROM scrobbles
        WHERE chat_id = ?
        AND created_at >= ?
        AND created_at <= ?
        ORDER BY created_at DESC
    """
    params = [chat_id, after, before]

    scrobble_summaries: list[ScrobbleSummary] = []
    async with conn.execute(query, params) as cursor:
        async for row in cursor:
            scrobble_summary = ScrobbleSummary(*row)
            scrobble_summaries.append(scrobble_summary)

    return scrobble_summaries
