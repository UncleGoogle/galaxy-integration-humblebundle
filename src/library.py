import time
import logging
import asyncio
from typing import Callable, Dict, List, Set, Iterable, Any, Coroutine, NamedTuple

from consts import SOURCE, NON_GAME_BUNDLE_TYPES, COMMA_SPLIT_BLACKLIST
from model.product import Product
from model.game import HumbleGame, Subproduct, Key, KeyGame
from model.types import GAME_PLATFORMS
from settings import LibrarySettings


logger = logging.getLogger(__name__)


class KeyInfo(NamedTuple):
    key: Key
    product_category: str


class LibraryResolver:
    NEXT_FETCH_IN = 3600 * 24 * 14

    def __init__(self, api, settings: LibrarySettings, save_cache_callback: Callable, cache: Dict[str, list]):
        self._api = api
        self._save_cache = save_cache_callback
        self._settings = settings
        self._cache = cache

    async def __call__(self, only_cache: bool = False) -> Dict[str, HumbleGame]:

        if not only_cache:
            await self._fetch_and_update_cache()

        # get all games in predefined order
        orders = list(self._cache.get('orders', {}).values())  # type: ignore[union-attr] - orders is always a dict
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
        sources = self._settings.sources

        if SOURCE.DRM_FREE in sources or SOURCE.KEYS in sources:
            next_fetch_orders = self._cache.get('next_fetch_orders')
            if next_fetch_orders is None or time.time() > next_fetch_orders:
                logger.info('Refreshing all orders')
                self._cache['orders'] = await self._fetch_orders([])
                self._cache['next_fetch_orders'] = time.time() + self.NEXT_FETCH_IN
            else:
                const_orders = {
                    gamekey: order
                    for gamekey, order in self._cache.get('orders', {}).items()
                    if self.__is_const(order)
                }
                self._cache.setdefault('orders', {}).update(await self._fetch_orders(const_orders))

        self._save_cache(self._cache)

    async def _fetch_orders(self, cached_gamekeys: Iterable[str]) -> Dict[str, dict]:
        gamekeys = await self._api.get_gamekeys()
        order_tasks = [self._api.get_order_details(x) for x in gamekeys if x not in cached_gamekeys]
        orders = await self.__gather_no_exceptions(order_tasks)
        orders = self.__filter_out_not_game_bundles(orders)
        return {order['gamekey']: order for order in orders}

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
    def __is_const(order):
        """Tells if this order can be safly cached or may change its content in the future"""
        if 'choices_remaining' in order and order['choices_remaining'] != 0:
            return False
        for key in order['tpkd_dict']['all_tpks']:
            if 'redeemed_key_val' not in key:
                return False
        return True

    @staticmethod
    def __filter_out_not_game_bundles(orders: list) -> list:
        filtered = []
        for details in orders:
            product = Product(details['product'])
            if product.bundle_type in NON_GAME_BUNDLE_TYPES:
                logger.info(f'Ignoring {details["product"]["machine_name"]} due bundle type: {product.bundle_type}')
                continue
            filtered.append(details)
        return filtered

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
