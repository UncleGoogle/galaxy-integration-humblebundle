import time
import logging
import asyncio
from typing import Callable, Dict, List, Set, Iterable

from consts import SOURCE, NON_GAME_BUNDLE_TYPES, GAME_PLATFORMS
from model.product import Product   
from model.game import HumbleGame, Subproduct, TroveGame, Key
from settings import LibrarySettings


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
            elif source == SOURCE.TROVE:
                all_games.extend(self._get_trove_games(self._cache.get('troves', [])))
            elif source == SOURCE.KEYS:
                all_games.extend(self._get_keys(orders, self._settings.show_revealed_keys))

        logging.info(f'all_games: {all_games}')

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
                logging.info('Refreshing all orders')
                self._cache['orders'] = await self._fetch_orders([])
                self._cache['next_fetch_orders'] = time.time() + self.NEXT_FETCH_IN
            else:
                const_orders = {
                    gamekey: order
                    for gamekey, order in self._cache.get('orders', {}).items()
                    if self.__all_keys_revealed(order)
                }
                self._cache.setdefault('orders', {}).update(await self._fetch_orders(const_orders))

        if SOURCE.TROVE in sources:
            next_fetch_troves = self._cache.get('next_fetch_troves')
            if next_fetch_troves is None or time.time() > next_fetch_troves:
                logging.info('Refreshing all troves')
                self._cache['troves'] = await self._fetch_troves([])
                self._cache['next_fetch_troves'] = time.time() + self.NEXT_FETCH_IN
            else:
                cached_troves = self._cache.get('troves', [])
                updated_troves = await self._fetch_troves(cached_troves)
                if updated_troves:
                    self._cache['troves'] = updated_troves

        self._save_cache(self._cache)

    async def _fetch_orders(self, cached_gamekeys: Iterable[str]) -> Dict[str, dict]:
        gamekeys = await self._api.get_gamekeys()
        order_tasks = [self._api.get_order_details(x) for x in gamekeys if x not in cached_gamekeys]
        orders = await asyncio.gather(*order_tasks)
        orders = self.__filter_out_not_game_bundles(orders)
        return {order['gamekey']: order for order in orders}
    
    async def _fetch_troves(self, cached_trove_data: list) -> list:
        troves_no = len(cached_trove_data)
        from_chunk = troves_no // self._api.TROVES_PER_CHUNK
        new_commers = await self._api.get_trove_details(from_chunk)
        new_troves_no = (len(new_commers) + from_chunk * self._api.TROVES_PER_CHUNK) - troves_no
        return cached_trove_data + new_commers[-new_troves_no:]
    
    @staticmethod
    def __all_keys_revealed(order):
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
                    logging.error(f"Error while parsing subproduct {repr(e)}: {sub_data}",  extra={'data': sub_data})
                    continue
        return subproducts

    @staticmethod
    def _get_trove_games(troves: list) -> List[TroveGame]:
        trove_games = []
        for trove in troves:
            try:
                trove_games.append(TroveGame(trove))
            except Exception as e:
                logging.error(f"Error while parsing troves {repr(e)}: {troves}", extra={'data': trove})
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
                    logging.error(f"Error while parsing tpks {repr(e)}: {tpks}", extra={'tpks': tpks})
                else:
                    if key.key_val is None or show_revealed_keys:
                        keys.append(key)
        return keys
