from typing import Optional


class Provider:
    def __init__(self, uri: Optional[str] = None) -> None:
        self.data = None
        self.uri = None
        self.title = None

    def has_valid_uri(self) -> bool:
        return self.uri is not None

    def is_not_found(self) -> bool:
        return self.data.not_found

    def fetch() -> None:
        pass

    def set_dj(self, dj: str) -> None:
        self.data.dj = dj

    def to_json(self) -> str:
        return self.data.to_json()

    def to_md(self) -> str:
        return self.data.to_md()
