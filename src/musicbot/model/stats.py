from dataclasses import dataclass


@dataclass
class UserStats:
    scrobbles: int
    fav_tags: list[tuple[str, int]]
    different_tags: int
