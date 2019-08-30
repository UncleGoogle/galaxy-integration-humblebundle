import enum
import logging
import asyncio
from typing import Callable, Dict, Any, List

from consts import SOURCE, NON_GAME_BUNDLE_TYPES, GAME_PLATFORMS
from model.product import Product   
from model.game import HumbleGame, Subproduct, TroveGame, Key
from settings import Settings


class Strategy(enum.Enum):
    FETCH = enum.auto()
    MIXED = enum.auto()
    CACHE = enum.auto()


class LibraryResolver:
    def __init__(self, api, settings: Settings, save_cache: Callable, cache: Dict[str, list]={}):
        self._api = api
        self._settings = settings
        self._save_cache = save_cache
        self._cache = cache
    
    async def __call__(self, strategy: Strategy) -> Dict[str, HumbleGame]:
        sources = self._settings.sources        
        show_revealed_keys = self._settings.show_revealed_keys

        if strategy == Strategy.FETCH:
            self._cache.clear()
            # await self._fetch_orders()
            # if had_subsciripitno: fetch_trove
        if strategy == Strategy.MIXED:
            pass
        if strategy == Strategy.CACHE:
            pass
        
        had_subscription = await self._api.had_trove_subscription()
        self._cache['orders'] = await self._fetch_orders()
        
        games = []
        for source in sources:
            if source == SOURCE.DRM_FREE:
                games.extend(self._get_subproducts(self._cache.get('orders')))
            elif source == SOURCE.TROVE:
                games.extend(self._get_trove_games(self._cache.get('troves')))
            elif source == SOURCE.KEYS:
                games.extend(self._get_keys(self._cache.get('orders'), show_revealed_keys))

        deduplicated = {}
        base_names = set()
        for game in games:
            if game.base_name not in base_names:
                base_names.add(game.base_name)
                deduplicated[game.machine_name] = game
        return deduplicated
    
    async def _fetch_orders(self) -> list:
        gamekeys = await self._api.get_gamekeys()
        order_tasks = [self._api.get_order_details(x) for x in gamekeys if x not in self._cache.get('gamekeys')]
        orders = await asyncio.gather(*order_tasks)
        return self.__filter_out_not_game_bundles(orders)
    
    @staticmethod
    def __filter_out_not_game_bundles(orders: list) -> list:
        filtered = []
        for details in orders:
            product = Product(details['product'])
            if product.bundle_type in NON_GAME_BUNDLE_TYPES:
                logging.info(f'Ignoring {details["product"]["machine_name"]} due bundle type: {product.bundle_type}')
                continue
            filtered.append(details)
        return filtered
    
    @staticmethod
    def _get_subproducts(orders: list) -> List[Subproduct]:
        subproducts = []
        for details in orders:
            for sub_data in details['subproducts']:
                try:
                    sub = Subproduct(sub_data)
                    if not set(sub.downloads).isdisjoint(GAME_PLATFORMS):
                        # at least one download exists for supported OS
                        subproducts.append(sub)
                except Exception as e:
                    logging.warning(f"Error while parsing downloads {e}: {details}")
                    continue
        return subproducts

    @staticmethod
    def _get_trove_games(troves: list) -> List[TroveGame]:
        trove_games = []
        for trove in troves:
            try:
                trove_games.append(TroveGame(trove))
            except Exception as e:
                logging.warning(f"Error while parsing troves {e}: {trove}")
                continue
        return trove_games

    @staticmethod
    def _get_keys(orders: list, show_revealed_keys: bool) -> List[Key]:
        keys = []
        for details in orders:
            for tpks in details['tpkd_dict']['all_tpks']:
                try:
                    key = Key(tpks)
                except Exception as e:
                    logging.warning(f"Error while parsing keys {e}: {tpks}")
                else:
                    if key.key_val is None or show_revealed_keys:
                        keys.append(key)
        return keys
