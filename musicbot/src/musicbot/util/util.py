from datetime import datetime, timedelta
from typing import List, Tuple, Union

from telegram.utils.helpers import escape_markdown


def escape_genre(genre: str) -> str:
    """Converts genre to something telegram can use as a tag."""
    return genre.replace(" ", "_").replace("-", "").replace("&", "_n_")


def parse_release_date(release_date: str) -> datetime:
    """Get the year out of a release date."""
    # we don't care about no stinking precision!
    return datetime.fromisoformat(f"{release_date.split('-')[0]}-01-01")


# just a shorthand
def _(str: str) -> str:
    return escape_markdown(str, 2)


def get_start_of_week() -> datetime:
    return datetime.now().replace(hour=0, minute=0, second=0) - timedelta(days=datetime.today().isoweekday() - 1)


def get_start_of_month() -> datetime:
    return datetime.now().replace(day=1)


def get_start_of_day() -> datetime:
    return datetime.now().replace(hour=0, minute=0, second=0)


def get_yesterday() -> Tuple[datetime, datetime]:
    start = datetime.now().replace(hour=5, minute=0, second=0) - timedelta(days=1)
    end = datetime.now().replace(hour=5, minute=0, second=0)
    return (start, end)


def get_timeframe(timeframe: str):
    timeframes = {
        "day": get_start_of_day,
        "week": get_start_of_week,
        "month": get_start_of_month,
        "yesterday": get_yesterday,
        "infinity": lambda: datetime(1900, 1, 1),
    }
    return timeframes[timeframe]()


def split_message(message: Union[List[str], str], num_lines: int = 15) -> List[str]:
    if type(message) == str:
        message = [message]
    while message[-1].count("\n") > num_lines:
        last_message = message.pop()
        split_message = last_message.split("\n", num_lines)
        message += ["\n".join(split_message[:-1]), split_message[-1]]
    return message
