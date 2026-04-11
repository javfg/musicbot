import sqlite3
from datetime import date
from enum import StrEnum

from musicbot.model.scrobble import ArtistType, ScrobbleType


class StrEnumAdapter:
    def __init__(self, enum_cls: type[StrEnum]):
        self.enum_cls = enum_cls

    def adapt(self, obj: StrEnum) -> str:
        return obj.value

    def convert(self, s: bytes) -> StrEnum:
        value = s.decode()
        return self.enum_cls(value)


def register_adapters():
    sta = StrEnumAdapter(ScrobbleType)
    ata = StrEnumAdapter(ArtistType)
    sqlite3.register_adapter(date, lambda d: d.isoformat())
    sqlite3.register_converter('date', lambda b: date.fromisoformat(b.decode()))
    sqlite3.register_adapter(StrEnum, lambda e: e.value)
    sqlite3.register_converter('scrobble_type', sta.convert)
    sqlite3.register_converter('artist_type', ata.convert)
