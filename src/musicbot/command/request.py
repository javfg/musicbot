from loguru import logger
from telegram import InlineQueryResultArticle, InputTextMessageContent, Update

from musicbot.context import MusicbotContext
from musicbot.security import secured


@secured
async def handle_request(update: Update, context: MusicbotContext) -> None:
    if update.inline_query is None:
        return
    query = update.inline_query.query.strip()
    if not query or len(query) < 3:
        return

    # first try to route to a specific provider
    results = []
    if provider := context.provider_registry.route(query):
        logger.info(f'routing query "{query}" to provider {provider.name}')
        try:
            results = await provider.search(query)
        except Exception as e:
            logger.error(f'error while searching for query "{query}" in provider {provider.name}: {e}')
            await update.inline_query.answer(
                results=[
                    InlineQueryResultArticle(
                        id='error',
                        title=str(e),
                        input_message_content=InputTextMessageContent(str(e)),
                    )
                ],
                cache_time=3600,
            )
    # then just search through the provider chain
    else:
        logger.info(f'searching for query "{query}" through provider chain')
        for sp in context.provider_registry.search_providers:
            logger.debug(f'searching for query "{query}" in provider {sp.name}')
            results = await sp.search(query)
            if results:
                logger.debug(f'{len(results)} results from {sp.name} for query "{query}"')
                break
            logger.debug(f'no results from {sp.name} for query "{query}"')

    # method that paginates results for telegram inline query
    def get_results(page_index: int = 0) -> list[InlineQueryResultArticle] | None:
        start = page_index * 10
        end = start + 10
        return [r.render() for r in results[start:end]] if start < len(results) else None

    await update.inline_query.answer(results=get_results, cache_time=3600, auto_pagination=True)
