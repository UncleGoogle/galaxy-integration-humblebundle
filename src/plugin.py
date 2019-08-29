import os
import sys
import time
import asyncio
import logging
import re
import webbrowser
import pathlib

sys.path.insert(0, str(pathlib.PurePath(__file__).parent / 'modules'))

import sentry_sdk
from galaxy.api.plugin import Plugin, create_and_run_plugin
from galaxy.api.consts import Platform
from galaxy.api.types import Authentication, NextStep, LocalGame

from version import __version__
from consts import GAME_PLATFORMS, NON_GAME_BUNDLE_TYPES, SOURCE
from settings import Settings
from webservice import AuthorizedHumbleAPI
from model.product import Product
from model.game import TroveGame, Subproduct, Key
from humbledownloader import HumbleDownloadResolver
from local import AppFinder


enable_sentry = False
if enable_sentry:
    sentry_sdk.init(
        "https://5b8ef07071c74c0a949169c1a8d41d1c@sentry.io/1514964",
        release=f"galaxy-integration-humblebundle@{__version__}"
    )


def report_problem(error, extra=None, level=logging.ERROR):
    logging.log(level, repr(error))
    with sentry_sdk.configure_scope() as scope:
        scope.set_extra("extra_context", extra)
        sentry_sdk.capture_exception(error)


AUTH_PARAMS = {
    "window_title": "Login to HumbleBundle",
    "window_width": 560,
    "window_height": 610,
    "start_uri": "https://www.humblebundle.com/login?goto=/home/library",
    # or https://www.humblebundle.com/account-start?goto=home"
    "end_uri_regex": "^" + re.escape("https://www.humblebundle.com/home/library")
}


class HumbleBundlePlugin(Plugin):
    def __init__(self, reader, writer, token):
        super().__init__(Platform.HumbleBundle, __version__, reader, writer, token)
        self._api = AuthorizedHumbleAPI()
        self._download_resolver = HumbleDownloadResolver()
        self._app_finder = AppFinder

        self._owned_games = {}
        self._local_games = {}
        self._cached_game_states = {}

        self._getting_owned_games = asyncio.Event()
        self._check_owned_task = asyncio.create_task(asyncio.sleep(0))
        self._check_installed_task = asyncio.create_task(asyncio.sleep(5))
        self._check_statuses_task = asyncio.create_task(asyncio.sleep(2))

        self.__under_instalation = set()

    def _save_cache(self, key: str, data: str):
        self.persistent_cache[key] = data
        self.push_cache()

    def handshake_complete(self):
        self._settings = Settings(
            config_dir=os.path.dirname(__file__),
            current_version=__version__,
            cached_version=self.persistent_cache.get('version'),
            cached_config=self.persistent_cache.get('config', ''),
            save_cache_callback=self._save_cache
        )

    async def authenticate(self, stored_credentials=None):
        if not stored_credentials:
            return NextStep("web_session", AUTH_PARAMS)

        logging.info('stored credentials found')
        user_id, user_name = await self._api.authenticate(stored_credentials)
        return Authentication(user_id, user_name)

    async def pass_login_credentials(self, step, credentials, cookies):
        auth_cookie = next(filter(lambda c: c['name'] == '_simpleauth_sess', cookies))

        user_id, user_name = await self._api.authenticate(auth_cookie)
        self.store_credentials(auth_cookie)
        return Authentication(user_id, user_name)

    async def _get_owned_games(self):
        gamekeys = await self._api.get_gamekeys()
        orders = [self._api.get_order_details(x) for x in gamekeys]

        start = time.time()
        all_games_details = await asyncio.gather(*orders)
        sentry_sdk.capture_message(f'Fetching info about {len(orders)} lasts: {time.time() - start}', level="info")

        games = []

        if SOURCE.TROVE in self._settings.sources and await self._api.had_trove_subscription():
            troves = await self._api.get_trove_details()
            for trove in troves:
                try:
                    games.append(TroveGame(trove))
                except Exception as e:
                    report_problem(e, trove, level=logging.WARNING)
                    continue

        for details in all_games_details:
            product = Product(details['product'])
            if product.bundle_type in NON_GAME_BUNDLE_TYPES:
                logging.info(f'Ignoring {details["product"]["machine_name"]} due bundle type: {product.bundle_type}')
                continue
            if SOURCE.DRM_FREE in self._settings.sources:
                for sub in details['subproducts']:
                    try:
                        prod = Subproduct(sub)
                        if not set(prod.downloads).isdisjoint(GAME_PLATFORMS):
                            # at least one download exists for supported OS
                            games.append(prod)
                    except Exception as e:
                        logging.warning(f"Error while parsing downloads {e}: {details}")
                        report_problem(e, details, level=logging.WARNING)
                        continue

            if SOURCE.KEYS in self._settings.sources:
                for tpks in details['tpkd_dict']['all_tpks']:
                    key = Key(tpks)
                    if key.key_val is None or self._settings.show_revealed_keys:
                        games.append(key)

        self._owned_games = {
            game.machine_name: game
            for game in games
        }

    async def get_owned_games(self):
        self._getting_owned_games.set()
        await self._get_owned_games()
        self._getting_owned_games.clear()
        return [g.in_galaxy_format() for g in self._owned_games.values()]

    async def install_game(self, game_id):
        if game_id in self.__under_instalation:
            return
        self.__under_instalation.add(game_id)

        try:
            game = self._owned_games.get(game_id)
            if game is None:
                raise RuntimeError(f'Install game: game {game_id} not found. Owned games: {self._owned_games.keys()}')

            if isinstance(game, Key):
                args = [str(pathlib.Path(__file__).parent / 'keysgui.py'),
                    game.human_name, game.key_type_human_name, str(game.key_val)
                ]
                process = await asyncio.create_subprocess_exec(sys.executable, *args,
                    stderr=asyncio.subprocess.PIPE)
                stdout_data, stderr_data = await process.communicate()
                if stderr_data:
                    logging.debug(args)
                    logging.debug(stderr_data)
            else:
                chosen_download = self._download_resolver(game)
                if isinstance(game, TroveGame):
                    url = await self._api.get_trove_sign_url(chosen_download, game.machine_name)
                    webbrowser.open(url['signed_url'])
                else:
                    webbrowser.open(chosen_download.web)

        except Exception as e:
            report_problem(e, extra=game)
            logging.exception(e)
        finally:
            self.__under_instalation.remove(game_id)

    async def get_local_games(self):
        if not self._app_finder or not self._owned_games:
            return []

        start = time.time()
        try:
            self._app_finder.refresh()
        except Exception as e:
            report_problem(e, None)
            return []

        local_games = await self._app_finder.find_local_games(list(self._owned_games.values()))
        self._local_games.update({game.machine_name: game for game in local_games})

        logging.debug(f'Refreshing local games took {time.time()-start}s')

        return [g.in_galaxy_format() for g in self._local_games.values()]

    async def launch_game(self, game_id):
        try:
            game = self._local_games[game_id]
        except KeyError as e:
            report_problem(e, {'local_games': self._local_games})
        else:
            game.run()

    async def uninstall_game(self, game_id):
        try:
            game = self._local_games[game_id]
        except KeyError as e:
            report_problem(e, {'local_games': self._local_games})
        else:
            game.uninstall()

    async def _check_owned(self):
        """ self.get_owned_games is called periodically by galaxy too rarely.
        This method check for new orders more often and also when relevant option in config file was changed.
        """
        # - cache all request responses on get_owned_games: orderlist && orders && trove && was_trove_subscriber
        # - on get_owned_games: refresh all; **use parsistent_cache; add 1week time counter after which run with mode 'reset'; otherwise run with 'optimized'
        #   filtered_owned_games = resolver(mode='reset')
        # - on changed config.owned: use cache.
        #   filtered_owned_games = resolver(mode='cache')
        # - on periodical check: refresh only things that may change: 
        #       - **was_trove_subscriber if was previously False; if true:
        #         - troves from last seen page + **(& go net only if len(lastpage) == 20) - this on webservice site,
        #       - orderlist; if new orders:
        #         - lacking orders,
        #       - all unrevealed keys orders to check if they has been revealed
        #   filtered_owned_games = resolver(mode='optimized', owned_games)
        # ** - optional; nice to have to maybe it is better to KISS than this optimization
        #
        # LibraryResolver.__init__(webservice, persistent_cache: dict, settings: dict, save_cache_callback)
        # LibraryResolver.__call__(mode: CacheStrategy, settings: dict) -> Dict[str, HumbleGame]  # deduplicated_owned_games
        #   
        old_library_settings = (self._settings.sources, self._settings.show_revealed_keys)
        self._settings.reload_local_config_if_changed()
        if old_library_settings != (self._settings.sources, self._settings.show_revealed_keys):
            logging.info(f'Config file library settings changed: {self._settings.sources} show_revealed_keys: {self._settings.show_revealed_keys}. Reparsing owned games')
            old_ids = self._owned_games.keys()
            await self._get_owned_games()

            for old_id in old_ids - self._owned_games.keys():
                self.remove_game(old_id)
            for new_id in self._owned_games.keys() - old_ids:
                self.add_game(self._owned_games[new_id].in_galaxy_format())


    async def _check_statuses(self):
        """Check satuses of already found installed (local) games.
        Detects events when game is:
        - launched (via Galaxy for now)
        - stopped
        - uninstalled
        """
        freezed_locals = list(self._local_games.values())
        for game in freezed_locals:
            state = game.state
            if state == self._cached_game_states.get(game.id):
                continue
            self.update_local_game_status(LocalGame(game.id, state))
            self._cached_game_states[game.id] = state
        await asyncio.sleep(0.5)

    async def _check_installed(self):
        """Searches for installed games and updates self._local_games"""
        await self.get_local_games()
        await asyncio.sleep(5)

    def tick(self):
        if self._check_owned_task.done() and not self._getting_owned_games.is_set():
            self._check_owned_task = asyncio.create_task(self._check_owned())

        if self._check_statuses_task.done():
            self._check_statuses_task = asyncio.create_task(self._check_statuses())

        if self._check_installed_task.done():
            self._check_installed_task = asyncio.create_task(self._check_installed())


    def shutdown(self):
        asyncio.create_task(self._api._session.close())


def main():
    create_and_run_plugin(HumbleBundlePlugin, sys.argv)

if __name__ == "__main__":
    main()

