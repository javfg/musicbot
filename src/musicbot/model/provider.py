import inspect
import re
from abc import ABC, abstractmethod
from collections.abc import Generator
from dataclasses import dataclass
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import ClassVar

from loguru import logger

from musicbot.config import Config
from musicbot.model.request import Request
from musicbot.model.scrobble import Scrobble, ScrobbleType


@dataclass
class Amender:
    pattern: str
    link_type: ScrobbleType
    link_key: str

    @property
    def name(self) -> str:
        return f'{self.link_type.value}.{self.link_key}'


@dataclass
class Route:
    pattern: re.Pattern
    provider: SearchableProvider


class Provider(ABC):
    name: ClassVar[str]
    """Unique name of the provider, e.g. 'spotify', 'youtube', etc."""
    weight: ClassVar[int]
    """The provider's weight. Higher means more relevant."""
    routes: ClassVar[list[str]]
    """List of regexes to route search queries to this provider."""
    amenders: ClassVar[list[Amender]]
    """List of amenders exposed by this provider."""

    @abstractmethod
    def __init__(
        self,
        settings: dict,
        provider_registry: ProviderRegistry,
        config: Config,
    ) -> None:
        """Initialize the provider with the given settings."""

    @abstractmethod
    async def fill(
        self,
        scrobble: Scrobble,
        provider_id: str | None,
    ) -> Scrobble:
        """Fill in the scrobble and return it."""
        return scrobble


class SearchableProvider(Provider, ABC):
    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int | None = None,
    ) -> list[Request]:
        """Search for the given query and return a list of request options."""


class ProviderRegistry:
    def __init__(self, config: Config):
        self.config = config
        self.providers: dict[str, Provider] = {}
        self.routes: list[Route] = []
        self.amenders: list[Amender] = []
        self.load_providers()

    def get(self, name: str) -> Provider:
        return self.providers[name]

    def get_all(self, original_provider_name: str) -> list[Provider]:
        """Get all providers in order of weight, and original provider first."""
        ps = sorted(
            self.providers.values(),
            key=lambda p: (p.name != original_provider_name, -p.weight),
        )
        logger.debug(f'getting all providers for {original_provider_name}: {[p.name for p in ps]}')
        return ps

    def route(self, query: str) -> SearchableProvider | None:
        for route in self.routes:
            if route.pattern.match(query):
                return route.provider
        return None

    @property
    def search_providers(self) -> Generator[SearchableProvider]:
        """Get all providers that implement the search method, in order of weight."""
        for provider_name in self.config.search_providers:
            if provider_name not in self.providers:
                raise ValueError(f'search provider {provider_name} specified in config not found in provider registry')
            provider = self.providers[provider_name]
            if isinstance(provider, SearchableProvider):
                yield provider

    def register_provider(self, provider: type[Provider]) -> None:
        provider_settings = {k: v for k, v in self.config.extra.items() if k.startswith(provider.name)}
        provider_instance = provider(
            settings=provider_settings,
            provider_registry=self,
            config=self.config,
        )
        self.providers[provider.name] = provider_instance
        logger.info(f'registered provider {provider.name} with weight {provider.weight}')
        for amender in provider_instance.amenders:
            self.amenders.append(amender)
            logger.info(
                f'added amender for provider {provider.name}: {amender.link_type}'
                f'{amender.link_key} with pattern {amender.pattern}'
            )
        if isinstance(provider_instance, SearchableProvider):
            for pattern in provider_instance.routes:
                self.routes.append(Route(re.compile(pattern), provider_instance))
                logger.info(f'added route for provider {provider.name}: {pattern}')

    def load_providers(self) -> None:
        provider_dir = Path(__file__).parent.parent / 'provider'
        logger.info(f'loading providers from {provider_dir}...')
        providers_to_register = []

        for provider_path in provider_dir.glob('[!__]*.py'):
            spec = spec_from_file_location(provider_path.stem, provider_path)
            if not spec or not spec.loader:
                raise ImportError(f'could not load provider {provider_path}')
            module = module_from_spec(spec)
            spec.loader.exec_module(module)
            for _, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, Provider) and obj is not Provider and obj is not SearchableProvider:
                    providers_to_register.append(obj)

        for obj in sorted(providers_to_register, key=lambda c: c.weight, reverse=True):
            self.register_provider(obj)
