import sys
import asyncio
import logging
import re
import webbrowser
import pathlib
import json
from dataclasses import astuple
from functools import partial
from typing import Any, Dict

sys.path.insert(0, str(pathlib.PurePath(__file__).parent / 'modules'))

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from galaxy.api.plugin import Plugin, create_and_run_plugin
from galaxy.api.consts import Platform
from galaxy.api.types import Authentication, NextStep, LocalGame
from galaxy.api.errors import AuthenticationRequired

from version import __version__
from settings import Settings
from webservice import AuthorizedHumbleAPI
from model.game import TroveGame, Key, Subproduct
from humbledownloader import HumbleDownloadResolver
from library import LibraryResolver
from local.appfinder import AppFinder


sentry_logging = LoggingIntegration(
    level=logging.INFO,
    event_level=logging.ERROR
)
sentry_sdk.init(
    dsn="https://76abb44bffbe45998dd304898327b718@sentry.io/1764525",
    integrations=[sentry_logging],
    release=f"hb-galaxy@{__version__}"
)


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
        self._app_finder = AppFinder()
        self._settings = None
        self._library_resolver = None

        self._owned_games = {}
        self._local_games = {}
        self._cached_game_states = {}

        self._getting_owned_games = asyncio.Lock()
        self._getting_local_games = asyncio.Lock()
        self._check_installed_task = asyncio.create_task(asyncio.sleep(5))
        self._check_statuses_task = asyncio.create_task(asyncio.sleep(2))

        self.__under_instalation = set()

    def _save_cache(self, key: str, data: Any):
        if type(data) != str:
            data = json.dumps(data)
        self.persistent_cache[key] = data
        self.push_cache()

    def handshake_complete(self):
        # tmp migration to fix 0.4.0 cache error
        library = json.loads(self.persistent_cache.get('library', '{}'))
        if library and type(library.get('orders')) == list:
            logging.info('Old cache migration')
            self._save_cache('library', {})

        self._settings = Settings(
            cache=self.persistent_cache,
            save_cache_callback=self.push_cache
        )
        self._library_resolver = LibraryResolver(
            api=self._api,
            settings=self._settings.library,
            cache=json.loads(self.persistent_cache.get('library', '{}')),
            save_cache_callback=partial(self._save_cache, 'library')
        )

    async def authenticate(self, stored_credentials=None):
        if not stored_credentials:
            return NextStep("web_session", AUTH_PARAMS)

        logging.info('Stored credentials found')
        user_id, user_name = await self._api.authenticate(stored_credentials)
        return Authentication(user_id, user_name)

    async def pass_login_credentials(self, step, credentials, cookies):
        auth_cookie = next(filter(lambda c: c['name'] == '_simpleauth_sess', cookies))

        user_id, user_name = await self._api.authenticate(auth_cookie)
        self.store_credentials(auth_cookie)
        return Authentication(user_id, user_name)

    async def get_owned_games(self):
        if not self._api.is_authenticated:
            raise AuthenticationRequired

        async with self._getting_owned_games:
            self._owned_games = await self._library_resolver()
            return [g.in_galaxy_format() for g in self._owned_games.values()]

    async def _prepare_local_games(self, paths_to_scan) -> Dict[str, LocalGame]:
        if not self._owned_games:
            logging.debug('-- Cannot scan for local gamPreparing local games: no owned games!')
            return {}

        owned_title_id = {v.human_name: k for k, v in self._owned_games.items() if not isinstance(v, Key)}
        return await self._app_finder.find_local_games(owned_title_id, paths_to_scan)

    async def get_local_games(self):
        # Owned games names are needed to local games search.
        # Galaxy calls orders on startup is unsupportive in such situation:
        # get_local_games - authenticate - get_local_games - get_owned_games
        # That is why plugin forces checking for owned games here
        if not self._owned_games:
            await self.get_owned_games()

        async with self._getting_local_games:
            self._local_games = await self._prepare_local_games(self._settings.installed.search_dirs)
            return [g.in_galaxy_format() for g in self._local_games.values()]

    async def install_game(self, game_id):
        if game_id in self.__under_instalation:
            return
        self.__under_instalation.add(game_id)

        game = self._owned_games.get(game_id)
        if game is None:
            logging.error(f'Install game: game {game_id} not found. Owned games: {self._owned_games.keys()}')
            return

        try:
            if isinstance(game, Key):
                args = [str(pathlib.Path(__file__).parent / 'keysgui.py'),
                    game.human_name, game.key_type_human_name, str(game.key_val)
                ]
                process = await asyncio.create_subprocess_exec(sys.executable, *args,
                    stderr=asyncio.subprocess.PIPE)
                _, stderr_data = await process.communicate()
                if stderr_data:
                    logging.debug(args)
                    logging.debug(stderr_data)
                return

            chosen_download = self._download_resolver(game)
            if isinstance(game, Subproduct):
                webbrowser.open(chosen_download.web)

            if isinstance(game, TroveGame):
                try:
                    url = await self._api.get_trove_sign_url(chosen_download, game.machine_name)
                except AuthenticationRequired:
                    logging.info('Looks like your Humble Monthly subscription has expired. Refer to config.ini to manage showed games.')
                    webbrowser.open('https://www.humblebundle.com/monthly/subscriber')
                else:
                    webbrowser.open(url['signed_url'])

        except Exception as e:
            logging.exception(e, extra={'game': game})
        finally:
            self.__under_instalation.remove(game_id)

    async def launch_game(self, game_id):
        try:
            game = self._local_games[game_id]
        except KeyError as e:
            logging.error(e, extra={'local_games': self._local_games})
        else:
            game.run()

    async def uninstall_game(self, game_id):
        try:
            game = self._local_games[game_id]
        except KeyError as e:
            logging.error(e, extra={'local_games': self._local_games})
        else:
            game.uninstall()

    async def _check_owned(self):
        async with self._getting_owned_games:
            old_ids = self._owned_games.keys()
            self._owned_games = await self._library_resolver(only_cache=True)
            for old_id in old_ids - self._owned_games.keys():
                self.remove_game(old_id)
            for new_id in self._owned_games.keys() - old_ids:
                self.add_game(self._owned_games[new_id].in_galaxy_format())

    async def _check_installed(self):
        """Non intensive for CPU check in Windows registry"""
        async with self._getting_local_games:
            local_games = await self._prepare_local_games(None)
            self._local_games.update(local_games)
        await asyncio.sleep(5)

    async def _check_statuses(self):
        """Checks satuses of local games. Detects events when game is:
        - installed (local games list updated in _check_installed)
        - uninstalled
        - launched (via Galaxy)
        - stopped
        """
        freezed_locals = list(self._local_games.values())
        for game in freezed_locals:
            state = game.state
            if state == self._cached_game_states.get(game.id):
                continue
            self.update_local_game_status(LocalGame(game.id, state))
            self._cached_game_states[game.id] = state
        await asyncio.sleep(0.5)

    def tick(self):
        old_lib_settings = astuple(self._settings.library)
        old_ins_settings = astuple(self._settings.installed)
        if self._settings.reload_local_config_if_changed():
            if old_lib_settings != astuple(self._settings.library):
                logging.info(f'Library settings has changed: {self._settings.library}')
                asyncio.create_task(self._check_owned())
            if old_ins_settings != self._settings.installed:
                logging.info(f'Installed settings has changed: {self._settings.installed}')
                asyncio.create_task(self.get_local_games())

        if self._check_installed_task.done():
            self._check_installed_task = asyncio.create_task(self._check_installed())

        if self._check_statuses_task.done():
            self._check_statuses_task = asyncio.create_task(self._check_statuses())

    def shutdown(self):
        asyncio.create_task(self._api.close_session())
        self._check_installed_task.cancel()
        self._check_statuses_task.cancel()


def main():
    create_and_run_plugin(HumbleBundlePlugin, sys.argv)

if __name__ == "__main__":
    main()

