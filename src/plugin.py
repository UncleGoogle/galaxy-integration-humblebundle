import sys
import asyncio
import logging
import re
import webbrowser
import pathlib
import json
from dataclasses import astuple
from functools import partial
from typing import Any, Optional

sys.path.insert(0, str(pathlib.PurePath(__file__).parent / 'modules'))

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from galaxy.api.plugin import Plugin, create_and_run_plugin
from galaxy.api.consts import Platform, OSCompatibility
from galaxy.api.types import Authentication, NextStep, LocalGame
from galaxy.api.errors import AuthenticationRequired, InvalidCredentials

from consts import HP, CURRENT_SYSTEM
from settings import Settings
from webservice import AuthorizedHumbleAPI
from model.game import TroveGame, Key, Subproduct
from humbledownloader import HumbleDownloadResolver
from library import LibraryResolver
from local import AppFinder
from privacy import SensitiveFilter
from utils.decorators import double_click_effect


with open(pathlib.Path(__file__).parent / 'manifest.json') as f:
    __version__ = json.load(f)['version']

logger = logging.getLogger()
logger.addFilter(SensitiveFilter())

sentry_logging = LoggingIntegration(
    level=logging.INFO,
    event_level=logging.ERROR
)
sentry_sdk.init(
    dsn="https://76abb44bffbe45998dd304898327b718@sentry.io/1764525",
    integrations=[sentry_logging],
    release=f"hb-galaxy@{__version__}"
)


class HumbleBundlePlugin(Plugin):
    def __init__(self, reader, writer, token):
        super().__init__(Platform.HumbleBundle, __version__, reader, writer, token)
        self._api = AuthorizedHumbleAPI()
        self._download_resolver = HumbleDownloadResolver()
        self._app_finder = AppFinder()
        self._settings = Settings()
        self._library_resolver = None

        self._owned_games = {}
        self._local_games = {}
        self._cached_game_states = {}

        self._getting_owned_games = asyncio.Lock()
        self._statuses_check: asyncio.Task = asyncio.create_task(asyncio.sleep(4))
        self._installed_check: asyncio.Task = asyncio.create_task(asyncio.sleep(4))

        self._rescan_needed = True
        self._under_instalation = set()

    def _save_cache(self, key: str, data: Any):
        if type(data) != str:
            data = json.dumps(data)
        self.persistent_cache[key] = data
        self.push_cache()
    
    def handshake_complete(self):
        self._settings.migration_from_cache(self.persistent_cache, self.push_cache)
        self._library_resolver = LibraryResolver(
            api=self._api,
            settings=self._settings.library,
            cache=json.loads(self.persistent_cache.get('library', '{}')),
            save_cache_callback=partial(self._save_cache, 'library')
        )

    async def authenticate(self, stored_credentials=None):
        if not stored_credentials:
            return NextStep("web_session", {
                    "window_title": "Login to HumbleBundle",
                    "window_width": 560,
                    "window_height": 610,
                    "start_uri": "https://www.humblebundle.com/login?goto=/home/library",
                    # or https://www.humblebundle.com/account-start?goto=home"
                    "end_uri_regex": "^" + re.escape("https://www.humblebundle.com/home/library")
                })

        logging.info('Stored credentials found')
        user_id = await self._api.authenticate(stored_credentials)
        if user_id is None:
            logging.debug('invalid creds')
            raise InvalidCredentials()
        return Authentication(user_id, user_id)

    async def pass_login_credentials(self, step, credentials, cookies):
        auth_cookie = next(filter(lambda c: c['name'] == '_simpleauth_sess', cookies))

        user_id = await self._api.authenticate(auth_cookie)
        self.store_credentials(auth_cookie)
        self._open_config()
        return Authentication(user_id, user_id)

    async def get_owned_games(self):
        if not self._api.is_authenticated:
            raise AuthenticationRequired()

        async with self._getting_owned_games:
            logging.debug('getting owned games')
            self._owned_games = await self._library_resolver()
            return [g.in_galaxy_format() for g in self._owned_games.values()]

    async def get_local_games(self):
        self._rescan_needed = True
        return [g.in_galaxy_format() for g in self._local_games.values()]

    def _open_config(self):
        self._settings.open_config_file()

    @double_click_effect(timeout=1, effect='_open_config')
    async def install_game(self, game_id):

        if game_id in self._under_instalation:
            return
        self._under_instalation.add(game_id)

        try:
            game = self._owned_games.get(game_id)
            if game is None:
                logging.error(f'Install game: game {game_id} not found. Owned games: {self._owned_games.keys()}')
                return

            if isinstance(game, Key):
                args = [str(pathlib.Path(__file__).parent / 'keysgui.py'),
                    game.human_name, game.key_type_human_name, str(game.key_val)
                ]
                process = await asyncio.create_subprocess_exec(sys.executable, *args, stderr=asyncio.subprocess.PIPE)
                _, stderr_data = await process.communicate()
                if stderr_data:
                    logging.error(f'Error for keygui: {stderr_data}', extra={'guiargs': args[:-1]})
                    webbrowser.open('https://www.humblebundle.com/home/keys')
                return

            chosen_download = self._download_resolver(game)
            if isinstance(game, Subproduct):
                webbrowser.open(chosen_download.web)

            if isinstance(game, TroveGame):
                try:
                    url = await self._api.get_trove_sign_url(chosen_download, game.machine_name)
                except AuthenticationRequired:
                    logging.info('Looks like your Humble Monthly subscription has expired. Refer to config.ini to manage showed games.')
                    webbrowser.open('https://www.humblebundle.com/subscription/home')
                else:
                    webbrowser.open(url['signed_url'])

        except Exception as e:
            logging.exception(e, extra={'game': game})
        finally:
            self._under_instalation.remove(game_id)

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

    async def get_os_compatibility(self, game_id: str, context: Any) -> Optional[OSCompatibility]:
        try:
            game = self._owned_games[game_id]
        except KeyError as e:
            logging.error(e, extra={'owned_games': self._owned_games})
            return None
        else:
            HP_OS_MAP = {
                HP.WINDOWS: OSCompatibility.Windows,
                HP.MAC: OSCompatibility.MacOS,
                HP.LINUX: OSCompatibility.Linux
            }
            osc = OSCompatibility(0)
            for platform in game.downloads:
                osc |= HP_OS_MAP.get(platform, OSCompatibility(0))
            return osc if osc else None

    async def _check_owned(self):
        async with self._getting_owned_games:
            old_ids = self._owned_games.keys()
            self._owned_games = await self._library_resolver(only_cache=True)
            for old_id in old_ids - self._owned_games.keys():
                self.remove_game(old_id)
            for new_id in self._owned_games.keys() - old_ids:
                self.add_game(self._owned_games[new_id].in_galaxy_format())

    async def _check_installed(self):
        """
        Owned games are needed to local games search. Galaxy methods call order is:
        get_local_games -> authenticate -> get_local_games -> get_owned_games (at the end!)
        That is why plugin sets all logic of getting local games in perdiodic checks
        """
        if not self._owned_games:
            logging.debug('Skipping perdiodic check for local games as owned games not found yet.')
            return

        owned_title_id = {
            game.human_name: uid for uid, game
            in self._owned_games.items()
            if not isinstance(game, Key) and game.os_compatibile(CURRENT_SYSTEM)
        }
        if self._rescan_needed:
            self._rescan_needed = False
            logging.debug(f'Checking installed games with path scanning in: {self._settings.installed.search_dirs}')
            self._local_games = await self._app_finder(owned_title_id, self._settings.installed.search_dirs)
        else:
            self._local_games.update(await self._app_finder(owned_title_id, None))
        await asyncio.sleep(4)

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
        if self._settings.reload_config_if_changed():
            if self._settings.library.has_changed():
                self.create_task(self._check_owned(), 'check owned')
            if self._settings.installed.has_changed():
                self._rescan_needed = True

        if self._installed_check.done():
            self._installed_check = asyncio.create_task(self._check_installed())

        if self._statuses_check.done():
            self._statuses_check = asyncio.create_task(self._check_statuses())

    async def shutdown(self):
        self._statuses_check.cancel()
        self._installed_check.cancel()
        self.create_task(self._api.close_session(), 'closing session')


def main():
    create_and_run_plugin(HumbleBundlePlugin, sys.argv)

if __name__ == "__main__":
    main()
