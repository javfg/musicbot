import asyncio
import os
import sys
from datetime import datetime, time, timedelta
from importlib.metadata import version
from threading import Thread

from bottle import route
from loguru import logger
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    InlineQueryHandler,
    JobQueue,
    MessageHandler,
    filters,
)

from musicbot.command import (
    ReplyToBotFilter,
    handle_amend,
    handle_daily_digest,
    handle_monthly_ranking,
    handle_ranking,
    handle_request,
    handle_scrobble,
    handle_stats,
    handle_updoot,
    handle_weekly_digest,
)
from musicbot.config import Config
from musicbot.context import MusicbotContext
from musicbot.db.store import StoreRegistry
from musicbot.errors import error_handler
from musicbot.model.provider import ProviderRegistry
from musicbot.util import get_next_saturday


class MusicBot:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.app = (
            Application
            .builder()
            .pool_timeout(config.provider_timeout)
            .read_timeout(config.provider_timeout)
            .write_timeout(config.provider_timeout)
            .context_types(ContextTypes(context=MusicbotContext))
            .token(config.bot_token)
            .post_init(self.setup)
            .post_stop(self.teardown)
            .build()
        )

    async def teardown(self, app: Application) -> None:
        logger.info('shutting down...')
        store_registry: StoreRegistry | None = app.bot_data.get('store_registry')
        if store_registry:
            await store_registry.close_all()
        else:
            logger.warning('store not found in bot_data during teardown')
        logger.info('shutdown complete')

    async def setup(self, app: Application) -> None:
        app.bot_data['config'] = self.config
        logger.info('initializing registries...')
        app.bot_data['provider_registry'] = ProviderRegistry(self.config)
        app.bot_data['store_registry'] = StoreRegistry.create(self.config)

        # app.job_queue is always there as long as the package is installed with the correct extras.
        self.job_queue: JobQueue = app.job_queue  # ty:ignore[invalid-assignment]

        reply_to_bot_filter = ReplyToBotFilter(app.bot.id)
        logger.info('setting up handlers...')

        app.add_error_handler(error_handler)

        app.add_handler(
            CommandHandler(
                'stats',
                callback=handle_stats,
            ),
        )
        app.add_handler(
            CommandHandler(
                'ranking',
                callback=handle_ranking,
            ),
        )
        app.add_handler(
            InlineQueryHandler(handle_request),
        )
        app.add_handler(
            MessageHandler(
                filters=filters.ViaBot(bot_id=app.bot.id) & filters.Regex(r'^🎧'),
                callback=handle_scrobble,
            )
        )
        app.add_handler(
            CallbackQueryHandler(
                pattern=r'^updoot:\d+$',
                callback=handle_updoot,
            )
        )
        app.add_handler(
            MessageHandler(
                filters=reply_to_bot_filter,
                callback=handle_amend,
            )
        )
        await app.bot.set_my_commands([
            ('ranking', 'Show DJ ranking'),
            ('stats', 'Show user statistics'),
        ])

        logger.info('scheduling digest jobs...')
        self.job_queue.run_daily(
            handle_daily_digest,
            time=time(10),
            name='daily_digest',
        )
        self.job_queue.run_repeating(
            handle_weekly_digest,
            interval=timedelta(days=7),
            first=get_next_saturday(),
            name='weekly_digest',
        )
        self.job_queue.run_monthly(
            handle_monthly_ranking,
            when=time(22),
            day=9,
            name='monthly_ranking',
        )

        logger.success(f'{self.config.bot_name} initialized successfully!')

    def run(self):
        self.app.run_polling()


def main() -> None:
    ver = version('musicbot')
    logger.info(f'starting musicbot v{ver}...')
    config = Config.from_env()

    if sys.argv[1:] and sys.argv[1] == '--migrate':
        from musicbot.db.migration import migrate

        asyncio.run(migrate(config))
        sys.exit(0)

    if config.env == 'production':
        logger.info('production instance, running with healthcheck')
        healthcheck_thread = Thread(target=start_healthcheck, args=(config,), daemon=True)
        healthcheck_thread.start()

    bot = MusicBot(config)
    bot.run()


@route('/health')
def health():
    pid: int = os.getpid()
    res: dict[str, str | int] = {'pid': pid, 'time': datetime.now().isoformat(), 'status': 'pass'}
    logger.debug(f'sending health check (pid: {pid})')
    return res


def start_healthcheck(config: Config):
    import bottle

    bottle._stderr = lambda *args, **kwargs: logger.debug(' '.join(str(a) for a in args).strip())  # ty:ignore[invalid-assignment]
    bottle.run(host=config.healthcheck_host, port=config.healthcheck_port)
