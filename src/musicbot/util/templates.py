from datetime import date

from telegram.helpers import escape_markdown


def _(content: str | date | None) -> str:
    """Escape characters for Telegram MarkdownV2 formatting."""
    if not content:
        return ''
    if isinstance(content, date):
        content = content.strftime('%Y-%m-%d')
    return escape_markdown(content, version=2)


def render_links(links: dict[str, str | None]) -> str:
    """Render a dictionary of platform links as a MarkdownV2 string."""
    rendered = []
    for platform, url in links.items():
        if url:
            rendered.append(f'[{_(platform)}]({_(url)})')
    return ' '.join(rendered) if rendered else 'N/A'


def render_tags(tags: list[str]) -> str:
    """Render a list of tags as a comma-separated string."""
    return ', '.join(_(tag) for tag in tags) if tags else 'N/A'
