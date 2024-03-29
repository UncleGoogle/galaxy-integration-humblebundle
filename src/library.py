from functools import reduce
from math import ceil
import logging
import asyncio
from typing import Callable, Dict, List, Sequence, Set, Iterable, Any, Coroutine, NamedTuple, TypeVar, Generator

from consts import SOURCE, NON_GAME_BUNDLE_TYPES, COMMA_SPLIT_BLACKLIST
from model.product import Product
from model.game import HumbleGame, Subproduct, Key, KeyGame
from model.types import GAME_PLATFORMS
from settings import LibrarySettings
from webservice import AuthorizedHumbleAPI


logger = logging.getLogger(__name__)


T = TypeVar('T')


class KeyInfo(NamedTuple):
    key: Key
    product_category: str


class LibraryResolver:
    ORDERS_CHUNK_SIZE = 35

    def __init__(
        self, 
        api: AuthorizedHumbleAPI,
        settings: LibrarySettings,
        save_cache_callback: Callable,
        cache: Dict[str, list]
    ):
        self._api = api
        self._save_cache = save_cache_callback
        self._settings = settings
        self._cache = cache

    async def __call__(self, only_cache: bool = False) -> Dict[str, HumbleGame]:

        if not only_cache:
            await self._fetch_and_update_cache()

        # get all games in predefined order
        orders = list(self._cache.get('orders', {}).values())  # type: ignore[union-attr]
        all_games: List[HumbleGame] = []
        for source in self._settings.sources:
            if source == SOURCE.DRM_FREE:
                all_games.extend(self._get_subproducts(orders))
            elif source == SOURCE.KEYS:
                all_games.extend(self._get_key_games(orders, self._settings.show_revealed_keys))

        logger.info(f'all_games: {all_games}')

        # deduplication of the games with the same title
        deduplicated: Dict[str, HumbleGame] = {}
        titles: Set[str] = set()
        for game in all_games:
            if game.human_name not in titles:
                titles.add(game.human_name)
                deduplicated[game.machine_name] = game
        return deduplicated

    async def _fetch_and_update_cache(self):
        logger.info('Refreshing all orders')
        self._cache['orders'] = await self._fetch_orders()
        self._save_cache(self._cache)

    async def _fetch_orders(self) -> Dict[str, dict]:
        gamekeys = await self._api.get_gamekeys()
        gamekey_chunks = self._make_chunks(gamekeys, size=self.ORDERS_CHUNK_SIZE)
        api_calls = [self._api.get_orders_bulk_details(chunk) for chunk in gamekey_chunks]
        call_results = await asyncio.gather(*api_calls)
        orders: Dict[str, Any] = reduce(lambda cum, nxt: {**cum, **nxt}, call_results, {})
        not_null_orders = {k: v for k, v in orders.items() if v is not None}
        filtered_orders = self.__filter_out_not_game_bundles(not_null_orders)
        return filtered_orders

    @staticmethod
    def _make_chunks(items: Sequence[T],  size: int) -> Generator[Sequence[T], None, None]:
        for i in range(ceil(len(items) / size)):
            yield items[i * size: (i + 1) * size]

    @staticmethod
    async def __gather_no_exceptions(tasks: Iterable[Coroutine]):
        """Wrapper around asyncio.gather(*args, return_exception=True)
        Returns list of non-exception items. If every item is exception, raise first of them, else logs them.
        Use case: https://github.com/UncleGoogle/galaxy-integration-humblebundle/issues/59
        """
        items = await asyncio.gather(*tasks, return_exceptions=True)
        if len(items) == 0:
            return []

        err: List[Exception] = []
        ok: List[Any] = []
        for it in items:
            (err if isinstance(it, Exception) else ok).append(it)

        if len(ok) == 0:
            raise err[0]
        if err and len(err) != len(items):
            logger.error(f'Exception(s) occured: [{err}].\nSkipping and going forward')
        return ok

    @staticmethod
    def __filter_out_not_game_bundles(orders: dict) -> dict:
        game_bundles = {}
        for gamekey, details in orders.items():
            product = Product(details['product'])
            if product.bundle_type in NON_GAME_BUNDLE_TYPES:
                logger.info(f'Ignoring {details["product"]["machine_name"]} due bundle type: {product.bundle_type}')
                continue
            game_bundles[gamekey] = details
        return game_bundles
    
    @staticmethod
    def _get_subproducts(orders: list) -> List[Subproduct]:
        subproducts = []
        for details in orders:
            for sub_data in details['subproducts']:
                sub = Subproduct(sub_data)
                try:
                    sub.in_galaxy_format()  # minimal validation
                except Exception as e:
                    logger.warning(f"Error while parsing subproduct {repr(e)}: {sub_data}",  extra={'data': sub_data})
                    continue
                if not set(sub.downloads).isdisjoint(GAME_PLATFORMS):
                    # at least one download exists for supported OS
                    subproducts.append(sub)
        return subproducts

    @staticmethod
    def _is_multigame_key(key: Key, product_category: str, blacklist: Iterable[str]) -> bool:
        if product_category != 'bundle':  # assuming only bundles contain multigame keys
            return False
        if ', ' not in key.human_name:
            return False
        for i in map(str.casefold, blacklist):
            if i in key.human_name.casefold():
                logger.debug(f'{key} split blacklisted by "{i}"')
                return False
        return True

    @staticmethod
    def _split_multigame_key(key: Key) -> List[KeyGame]:
        """Extract list of KeyGame objects from single Key"""
        logger.info(f'Spliting {key}')
        names = key.human_name.split(', ')
        games = []

        for i, name in enumerate(names):
            # Multi-game packs have the word "and" in front of the last game name
            first, _, rest = name.partition(" ")
            if first == "and": name = rest or first
            games.append(KeyGame(key, f'{key.machine_name}_{i}', name))
        return games

    @staticmethod
    def _get_key_infos(orders: list) -> List[KeyInfo]:
        keys = []
        for details in orders:
            for tpks in details['tpkd_dict']['all_tpks']:
                key = Key(tpks)
                try:
                    key.in_galaxy_format()  # minimal validation
                    product_category = details['product']['category']
                except Exception as e:
                    logger.warning(f"Error while parsing tpks {repr(e)}: {tpks}", extra={'tpks': tpks})
                    continue
                else:
                    keys.append(KeyInfo(key, product_category))
        return keys

    def _get_key_games(self, orders: list, show_revealed_keys: bool) -> List[KeyGame]:
        key_games = []
        key_infos = self._get_key_infos(orders)
        for key, product_category in key_infos:
            if key.key_val is None or show_revealed_keys:
                if self._is_multigame_key(key, product_category, blacklist=COMMA_SPLIT_BLACKLIST):
                    key_games.extend(self._split_multigame_key(key))
                else:
                    key_games.append(KeyGame(key, key.machine_name, key.human_name))
        return key_games
