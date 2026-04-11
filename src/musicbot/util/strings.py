import re


def clean(text: str) -> str:
    """Clean a string for using in a search query."""
    # remove bracketed/parenthesized noise
    text = re.sub(r'[\(\[\{][^\)\]\}]*[\)\]\}]', '', text)
    # remove common noise words
    text = re.sub(
        r'\b(original|soundtrack|official|music|video|mv|lyric|lyrics|audio|hd|4k|clip|live)\b',
        '',
        text,
        flags=re.IGNORECASE,
    )
    # remove special chars except dash
    text = re.sub(r'[^\w\s\-]', '', text)
    # collapse whitespace
    return re.sub(r'\s+', ' ', text).strip()
