from musicbot.model.scrobble import ArtistType, ScrobbleType

PRAGMA_STATEMENTS = [
    'PRAGMA foreign_keys = ON',
    'PRAGMA journal_mode = WAL',
]

scrobble_type_v = ', '.join(f"'{t.value}'" for t in ScrobbleType)
artist_type_v = ', '.join(f"'{t.value}'" for t in ArtistType)

TABLE_STATEMENTS = [
    f"""
        CREATE TABLE IF NOT EXISTS scrobbles (
            id INTEGER PRIMARY KEY,
            dj TEXT NOT NULL,
            dj_id INTEGER NOT NULL,
            chat_id INTEGER NOT NULL,
            message_id INTEGER NOT NULL,
            message_content TEXT NOT NULL,
            scrobble_type scrobble_type NOT NULL CHECK (scrobble_type IN ({scrobble_type_v})),
            updoots INTEGER DEFAULT 0,

            artist_name TEXT NOT NULL,
            artist_type TEXT CHECK (artist_type IN ({artist_type_v})),
            artist_area TEXT,
            artist_area_born TEXT,
            artist_area_died TEXT,
            artist_born DATE,
            artist_died DATE,
            artist_thumbnail_url TEXT,
            artist_links TEXT,

            album_title TEXT,
            album_release_date DATE,
            album_thumbnail_url TEXT,
            album_links TEXT,

            track_title TEXT,
            track_release_date DATE,
            track_duration INTEGER,
            track_isrc TEXT,
            track_links TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            deleted BOOLEAN DEFAULT 0
        );
    """,
    """
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """,
    """
        CREATE TABLE IF NOT EXISTS artist_tags (
            scrobble_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            dj_id INTEGER NOT NULL,
            PRIMARY KEY (scrobble_id, tag_id),
            FOREIGN KEY (scrobble_id) REFERENCES scrobbles (id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags (id)
        );
    """,
    """
        CREATE TABLE IF NOT EXISTS album_tags (
            scrobble_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            PRIMARY KEY (scrobble_id, tag_id),
            FOREIGN KEY (scrobble_id) REFERENCES scrobbles (id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags (id)
        );
    """,
    """
        CREATE TABLE IF NOT EXISTS updoots (
            scrobble_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            PRIMARY KEY (scrobble_id, user_id),
            FOREIGN KEY (scrobble_id) REFERENCES scrobbles (id) ON DELETE CASCADE
        );
    """,
]

INDEX_STATEMENTS = [
    'CREATE INDEX IF NOT EXISTS idx_scrobbles_chat_created ON scrobbles (chat_id, created_at)',
    'CREATE INDEX IF NOT EXISTS idx_scrobbles_dj_id ON scrobbles (dj_id)',
    'CREATE INDEX IF NOT EXISTS idx_scrobbles_message_id ON scrobbles (message_id)',
    'CREATE INDEX IF NOT EXISTS idx_artist_tags_dj_id ON artist_tags (dj_id)',
]

setup_statements = PRAGMA_STATEMENTS + TABLE_STATEMENTS + INDEX_STATEMENTS
