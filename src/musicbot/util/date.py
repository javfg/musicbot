from datetime import date, datetime, timedelta

from loguru import logger


def date_from_iso(iso_str: str | None) -> date | None:
    """Convert an ISO date string to a date object."""
    if iso_str is None:
        return None

    if iso_str:
        try:
            return date.fromisoformat(iso_str)
        except ValueError:
            try:
                return date(int(iso_str), 1, 1)
            except ValueError:
                try:
                    year, month = iso_str.split('-')
                    return date(int(year), int(month), 1)
                except ValueError:
                    logger.warning(f'unable to parse release date: {iso_str}')
                    return None

    return None


def get_next_saturday(
    hour: int = 22,
    minute: int = 0,
    second: int = 0,
) -> datetime:
    today = datetime.now().replace(hour=hour, minute=minute, second=second)
    delta = timedelta((12 - today.weekday()) % 7)
    return today + delta


def get_timeframe(timeframe: str) -> datetime:
    now = datetime.now()
    timeframes = {
        'day': now.replace(hour=0, minute=0, second=0) - timedelta(days=1),
        'week': now.replace(hour=0, minute=0, second=0) - timedelta(days=now.weekday()),
        'month': now.replace(hour=0, minute=0, second=0, day=1),
        'infinite': datetime.min,
    }
    return timeframes[timeframe]
