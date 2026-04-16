import os
import sys
from dataclasses import dataclass, fields
from datetime import datetime
from importlib.metadata import metadata
from pathlib import Path
from typing import Literal, cast

from dotenv import load_dotenv
from loguru import logger

type LogLevel = Literal['TRACE', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']


def must_str(env_var: str) -> str:
    value = os.environ.get(env_var)
    if value is None:
        raise ValueError(f'missing required environment variable {env_var}')
    return value


def must_list(env_var: str) -> list[int]:
    value = os.environ.get(env_var)
    if value is None:
        raise ValueError(f'missing required environment variable {env_var}')
    return [int(x.strip()) for x in value.split(',') if x.strip()]


PROVIDER_CACHE_SIZE = 8192
PROVIDER_CACHE_TTL = 60 * 60 * 24 * 7  # 7 days


@dataclass
class Config:
    env: str
    bot_name: str
    bot_token: str
    db_path: Path
    log_level: LogLevel
    log_path: Path
    healthcheck_host: str
    healthcheck_port: int
    chat_id_whitelist: list[int]
    chat_id_errors: int | None
    allowlist_cache_ttl: int
    search_providers: list[str]
    preferred_previews: list[str]
    user_agent: str
    provider_timeout: int
    extra: dict[str, str]

    @classmethod
    def from_env(cls) -> Config:
        env_loaded = load_dotenv()
        if env_loaded:
            logger.info('config .env file loaded successfully')
        else:
            logger.warning('config .env file not found')

        log_level = cast(LogLevel, os.environ.get('MUSICBOT_LOG_LEVEL', 'INFO'))
        log_path = Path(os.environ.get('MUSICBOT_LOG_PATH', './logs'))

        logger.remove()
        logger.add(sink=sys.stderr, level=log_level)
        logger.add(
            sink=log_path / f'{datetime.now().strftime("%Y-%m-%d")}.log',
            level=log_level,
            rotation='6 months',
            compression='zip',
        )

        m = metadata('musicbot')
        version = m['Version']
        author_email = m['Author-email']
        user_agent = f'MusicBot/{version} ( {author_email} )'

        self = cls(
            env=os.environ.get('MUSICBOT_ENV', 'production'),
            bot_name=must_str('MUSICBOT_BOT_NAME'),
            bot_token=must_str('MUSICBOT_BOT_TOKEN'),
            db_path=Path(os.environ.get('MUSICBOT_DB_PATH', './data')),
            log_level=log_level,
            log_path=log_path,
            healthcheck_host=os.environ.get('MUSICBOT_HEALTHCHECK_HOST', '127.0.0.1'),
            healthcheck_port=int(os.environ.get('MUSICBOT_HEALTHCHECK_PORT', '8080')),
            chat_id_whitelist=must_list('MUSICBOT_CHAT_ID_WHITELIST'),
            chat_id_errors=int(os.environ.get('MUSICBOT_CHAT_ID_ERRORS', '0')) or None,
            allowlist_cache_ttl=int(os.environ.get('MUSICBOT_ALLOWLIST_CACHE_TTL', str(60 * 60 * 24 * 7))),
            search_providers=os.environ.get('MUSICBOT_SEARCH_PROVIDERS', 'deezer,musicbrainz').split(','),
            preferred_previews=os.environ.get('MUSICBOT_PREFERRED_PREVIEWS', 'youtube,spotify,musicbrainz').split(','),
            user_agent=os.environ.get('MUSICBOT_USER_AGENT', user_agent),
            provider_timeout=int(os.environ.get('MUSICBOT_PROVIDER_TIMEOUT', str(30))),
            extra={},
        )

        self.extra = {
            'spotify_client_id': must_str('MUSICBOT_SPOTIFY_CLIENT_ID'),
            'spotify_client_secret': must_str('MUSICBOT_SPOTIFY_CLIENT_SECRET'),
            'genius_access_token': must_str('MUSICBOT_GENIUS_ACCESS_TOKEN'),
        }

        logger.info('config parsed successfully')
        for f in [fi for fi in fields(self) if fi.name not in ['bot_token', 'extra']]:
            logger.info(f'{f.name:<{20}}: {getattr(self, f.name)}')

        return self
