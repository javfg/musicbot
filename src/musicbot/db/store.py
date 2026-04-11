import sqlite3
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import aiosqlite
from loguru import logger

from musicbot.db.adapters import register_adapters
from musicbot.db.schema import setup_statements


class Store:
    def __init__(self, conn: aiosqlite.Connection) -> None:
        self.conn = conn

    @classmethod
    async def create(cls, db_path: Path, chat_id: int) -> Store:
        db_path.mkdir(parents=True, exist_ok=True)
        conn = await aiosqlite.connect(
            database=str(db_path / f'{chat_id}.sqlite'),
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        store = cls(conn)
        await store._setup_db()
        return store

    async def _setup_db(self) -> None:
        for statement in setup_statements:
            await self.conn.execute(statement)
        await self.conn.commit()

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[aiosqlite.Connection]:
        try:
            yield self.conn
            await self.conn.commit()
        except Exception:
            await self.conn.rollback()
            raise

    async def close(self) -> None:
        await self.conn.close()


class StoreRegistry:
    def __init__(self, base_path: Path) -> None:
        self.base_path = base_path
        self._stores = {}

    @classmethod
    def create(cls, config) -> StoreRegistry:
        register_adapters()
        return cls(config.db_path)

    async def get(self, chat_id: int) -> Store:
        if chat_id not in self._stores:
            logger.info(f'creating store for chat_id {chat_id}')
            self._stores[chat_id] = await Store.create(self.base_path, chat_id)
        return self._stores[chat_id]

    async def close_all(self) -> None:
        for store in self._stores.values():
            await store.close()
        self._stores.clear()
