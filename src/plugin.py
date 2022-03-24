import sys
import platform
import asyncio
import logging
import re
import webbrowser
import pathlib
import json
import calendar
import typing as t
from functools import partial
from distutils.version import LooseVersion

sys.path.insert(0, str(pathlib.PurePath(__file__).parent / 'modules'))

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from galaxy.api.plugin import Plugin, create_and_run_plugin
from galaxy.api.consts import Platform, OSCompatibility
from galaxy.api.types import Authentication, NextStep, LocalGame, GameLibrarySettings, Subscription
from galaxy.api.errors import AuthenticationRequired, UnknownBackendResponse, UnknownError, BackendError

from consts import IS_WINDOWS, TROVE_SUBSCRIPTION_NAME
from settings import Settings
from webservice import AuthorizedHumbleAPI
from model.game import TroveGame, Key, Subproduct, HumbleGame, ChoiceGame
from model.types import HP
from humbledownloader import HumbleDownloadResolver
from library import LibraryResolver
from local import AppFinder
from privacy import SensitiveFilter
from active_month_resolver import (
    ActiveMonthInfoByUser,
    ActiveMonthResolver,
)
from utils.decorators import double_click_effect
from gui.options import OPTIONS_MODE
import guirunner as gui


with open(pathlib.Path(__file__).parent / 'manifest.json') as f:
    __version__ = json.load(f)['version']

logger = logging.getLogger()
logger.addFilter(SensitiveFilter())


def setup_sentry():
    sentry_logging = LoggingIntegration(
        level=logging.INFO,
        event_level=logging.ERROR
    )
    sentry_sdk.init(
        dns="https://40919944b74b4cc49bf94c482f013533@o284798.ingest.sentry.io/3976593",
        traces_sample_rate=0.1,
        integrations=[sentry_logging],
        release=f"hb-galaxy@{__version__}"
    )


class HumbleBundlePlugin(Plugin):
    def __init__(self, reader, writer, token):
        super().__init__(Platform.HumbleBundle, __version__, reader, writer, token)
        headers = {"User-Agent": f"HumbleBundle plugin for GOG Galaxy 2.0 v{__version__}"}
        self._api = AuthorizedHumbleAPI(headers=headers)
        self._download_resolver = HumbleDownloadResolver()
        self._app_finder = AppFinder()
        self._settings = Settings()
        self._library_resolver = None

        self._owned_games: t.Dict[str, HumbleGame] = {}
        self._trove_games: t.Dict[str, TroveGame] = {}  # legacy - for loading already existing cache
        self._choice_games: t.Dict[str, ChoiceGame] = {}

        self._local_games = {}
        self._cached_game_states = {}

        self._getting_owned_games = asyncio.Lock()
        self._owned_check: asyncio.Task = asyncio.create_task(asyncio.sleep(8))
        self._statuses_check: asyncio.Task = asyncio.create_task(asyncio.sleep(4))
        self._installed_check: asyncio.Task = asyncio.create_task(asyncio.sleep(4))

        self._rescan_needed = True
        self._under_installation = set()

    @property
    def _humble_games(self) -> t.Dict[str, HumbleGame]:
        """
        Alias for cached owned and subscription games mapped by id.
        In case of id duplication, owned games got priority.
        """
        return {
            **self._choice_games,
            **self._trove_games,
            **self._owned_games
        }

    def _save_cache(self, key: str, data: t.Any):
        data = json.dumps(data)
        self.persistent_cache[key] = data
        self.push_cache()

    def _load_cache(self, key: str, default: t.Any=None) -> t.Any:
        if key in self.persistent_cache:
            return json.loads(self.persistent_cache[key])
        return default

    def handshake_complete(self):
        self._library_resolver = LibraryResolver(
            api=self._api,
            settings=self._settings.library,
            cache=self._load_cache('library', {}),
            save_cache_callback=partial(self._save_cache, 'library')
        )
        self._last_version = self._load_cache('last_version', default=None)
        self._trove_games = {g['machine_name']: TroveGame(g) for g in self._load_cache('trove_games', [])}
        self._choice_games = {g['id']: ChoiceGame(**g) for g in self._load_cache('choice_games', [])}
    
    async def _get_user_name(self) -> str:
        try:
            marketing_data = await self._api.get_main_page_webpack_data()
            return marketing_data['userOptions']['email'].split('@')[0]
        except (BackendError, KeyError, UnknownBackendResponse) as e:
            logger.error(repr(e))
            return ""
    
    async def _do_auth(self, auth_cookie) -> Authentication:
        user_id = await self._api.authenticate(auth_cookie)
        user_name = await self._get_user_name() or "Humble User"
        return Authentication(user_id, user_name)

    async def authenticate(self, stored_credentials=None):
        show_news = self.__is_after_minor_update()
        self._save_cache('last_version', __version__)

        if not stored_credentials:
            return NextStep("web_session", {
                    "window_title": "Login to HumbleBundle",
                    "window_width": 560,
                    "window_height": 610,
                    "start_uri": "https://www.humblebundle.com/login?goto=/home/library",
                    "end_uri_regex": "^" + re.escape("https://www.humblebundle.com/home/library")
                })

        logging.info('Stored credentials found')
        auth: Authentication = await self._do_auth(stored_credentials)
        
        if show_news:
            self._open_config(OPTIONS_MODE.NEWS)
        return auth

    async def pass_login_credentials(self, step, credentials, cookies):
        auth_cookie = next(filter(lambda c: c['name'] == '_simpleauth_sess', cookies))
        auth: Authentication = await self._do_auth(auth_cookie)
        self.store_credentials(auth_cookie)
        self._open_config(OPTIONS_MODE.WELCOME)
        return auth

    def __is_after_minor_update(self) -> bool:
        def cut_to_minor(ver: str) -> LooseVersion:
            """3 part version assumed"""
            return LooseVersion(ver.rsplit('.', 1)[0])
        return self._last_version is None \
            or cut_to_minor(__version__) > cut_to_minor(self._last_version)

    async def get_owned_games(self):
        if not self._api.is_authenticated:
            raise AuthenticationRequired()

        async with self._getting_owned_games:
            logging.debug('getting owned games')
            self._owned_games = await self._library_resolver()
            return [g.in_galaxy_format() for g in self._owned_games.values()]

    @staticmethod
    def _normalize_subscription_name(machine_name: str):
        month_map = {
            'january': '01',
            'february': '02',
            'march': '03',
            'april': '04',
            'may': '05',
            'june': '06',
            'july': '07',
            'august': '08',
            'september': '09',
            'october': '10',
            'november': '11',
            'december': '12'
        }
        try:
            month, year, type_ = machine_name.split('_')
        except Exception:
            assert False, f"is {machine_name}"
        return f'Humble {type_.title()} {year}-{month_map[month]}'

    @staticmethod
    def _choice_name_to_slug(subscription_name: str):
        _, _, year_month = subscription_name.split(' ')
        year, month = year_month.split('-')
        return f'{calendar.month_name[int(month)]}-{year}'.lower()

    async def get_subscriptions(self):
        subscriptions: t.List[Subscription] = []
        subscription_state = await self._api.get_user_subscription_state()
        has_active_perks = subscription_state.get("perksStatus") == "active"

        active_content_checked = False
        async for product in self._api.get_subscription_products_with_gamekeys():
            if 'contentChoiceData' not in product:
                break  # all Humble Choice months already yielded
            is_product_unlocked = 'gamekey' in product
            active_content_checked |= product.get('isActiveContent', False)
            subscriptions.append(Subscription(
                self._normalize_subscription_name(product['productMachineName']),
                owned = is_product_unlocked
            ))

        if not active_content_checked:
            active_month_resolver = ActiveMonthResolver(has_active_perks)
            active_month_info: ActiveMonthInfoByUser = await active_month_resolver.resolve(self._api)
            
            if active_month_info.machine_name:
                subscriptions.append(Subscription(
                    self._normalize_subscription_name(active_month_info.machine_name),
                    owned = active_month_info.is_or_will_be_owned,
                    end_time = None  # #117: get_last_friday.timestamp() if user_plan not in [None, Lite] else None
                ))

        return subscriptions
    
    async def get_subscription_games(self, subscription_name, context):
        if subscription_name == TROVE_SUBSCRIPTION_NAME:
            raise UnknownError("Plugin does not support Trove games any longer")

        choice_slug = self._choice_name_to_slug(subscription_name)
        choice_data = await self._api.get_choice_content_data(choice_slug)
        cco = choice_data.content_choice_options
        show_all = cco.remaining_choices != 0

        choice_games: t.Dict[str, ChoiceGame] = {
            ch.id: ChoiceGame(ch.id, ch.title, choice_slug)
            for ch in cco.content_choices
            if show_all or ch.id in cco.content_choices_made
        }
        choice_games.update({
            extr.machine_name: ChoiceGame(extr.machine_name, extr.human_name, choice_slug, is_extras=True)
            for extr in cco.extrases
        })
        self._choice_games.update(choice_games)
        yield [game.in_galaxy_format() for game in choice_games.values()]

    def subscription_games_import_complete(self):
        self._save_cache('choice_games', [game.serialize() for game in self._choice_games.values()])

    async def get_local_games(self):
        self._rescan_needed = True
        return [g.in_galaxy_format() for g in self._local_games.values()]

    def _open_config(self, mode: OPTIONS_MODE=OPTIONS_MODE.NORMAL):
        """Synchonious wrapper for self._open_config_async"""
        self.create_task(self._open_config_async(mode), 'opening config')

    async def _open_config_async(self, mode: OPTIONS_MODE):
        try:
            await gui.show_options(mode)
        except Exception as e:
            logging.exception(e)
            self._settings.save_config()
            self._settings.open_config_file()

    @double_click_effect(timeout=0.5, effect='_open_config')
    async def install_game(self, game_id):
        if game_id in self._under_installation:
            return

        self._under_installation.add(game_id)
        try:
            game = self._humble_games.get(game_id)
            if game is None:
                logging.error(f'Install game: game {game_id} not found. Humble games: {self._humble_games.keys()}')
                return

            if isinstance(game, ChoiceGame):
                webbrowser.open(game.presentation_url)
                return

            if isinstance(game, Key):
                try:
                    await gui.show_key(game)
                except Exception as e:
                    logging.error(e, extra={'platform_info': platform.uname()})
                    webbrowser.open('https://www.humblebundle.com/home/keys')
                return

            try:
                hp = HP.WINDOWS if IS_WINDOWS else HP.MAC
                curr_os_download = game.downloads[hp]
            except KeyError:
                raise UnknownError(f'{game.human_name} has only downloads for {list(game.downloads.keys())}')

            if isinstance(game, Subproduct):
                chosen_download_struct = self._download_resolver(curr_os_download)
                urls = await self._api.sign_url_subproduct(chosen_download_struct, curr_os_download.machine_name)
                webbrowser.open(urls['signed_url'])

        except Exception as e:
            logging.error(e, extra={'game': game})
            raise
        finally:
            self._under_installation.remove(game_id)

    async def get_game_library_settings(self, game_id: str, context: t.Any) -> GameLibrarySettings:
        gls = GameLibrarySettings(game_id, None, None)
        game = self._humble_games[game_id]
        if isinstance(game, Key):
            gls.tags = ['Key']
            if game.key_val is None:
                gls.tags.append('Unrevealed')
        if isinstance(game, TroveGame):
            gls.tags = []  # remove redundant tags since Galaxy support for subscripitons
        return gls

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

    async def get_local_size(self, game_id, context) -> t.Optional[int]:
        try:
            game = self._local_games[game_id]
        except KeyError as e:
            logging.error(e, extra={'local_games': self._local_games})
            return None
        return await game.get_size()

    async def get_os_compatibility(self, game_id: str, context: t.Any) -> t.Optional[OSCompatibility]:
        try:
            game = self._humble_games[game_id]
        except KeyError as e:
            logging.error(e, extra={'humble_games': self._humble_games})
            return None

        # treat keys as os independent (enables Install button)
        if isinstance(game, Key):
            return OSCompatibility(0b111)

        HP_OS_MAP = {
            HP.WINDOWS: OSCompatibility.Windows,
            HP.MAC: OSCompatibility.MacOS,
            HP.LINUX: OSCompatibility.Linux
        }
        osc = OSCompatibility(0)
        for humble_platform in game.downloads:
            osc |= HP_OS_MAP.get(humble_platform, OSCompatibility(0))
        return osc if osc else None

    async def _check_owned(self):
        async with self._getting_owned_games:
            old_ids = self._owned_games.keys()
            self._owned_games = await self._library_resolver(only_cache=True)
            for old_id in old_ids - self._owned_games.keys():
                self.remove_game(old_id)
            for new_id in self._owned_games.keys() - old_ids:
                self.add_game(self._owned_games[new_id].in_galaxy_format())
        # increased throttle to protect Galaxy from quick & heavy library changes
        await asyncio.sleep(3)

    async def _check_installed(self):
        """
        Owned games are needed to local games search. Galaxy methods call order is:
        get_local_games -> authenticate -> get_local_games -> get_owned_games (at the end!).
        That is why the plugin sets all logic of getting local games in perdiodic checks like this one.
        """
        if not self._owned_games:
            logging.debug('Skipping perdiodic check for local games as owned games not found yet.')
            return

        hp = HP.WINDOWS if IS_WINDOWS else HP.MAC
        installable_title_id = {
            game.human_name: uid for uid, game
            in {**self._owned_games, **self._trove_games}.items()
            if game.os_compatibile(hp)
        }
        if self._rescan_needed:
            self._rescan_needed = False
            logging.debug(f'Checking installed games with path scanning in: {self._settings.installed.search_dirs}')
            self._local_games = await self._app_finder(installable_title_id, self._settings.installed.search_dirs)
        else:
            self._local_games.update(await self._app_finder(installable_title_id, None))
        await asyncio.sleep(4)

    async def _check_statuses(self):
        """Checks satuses of local games. Detects changes in local games when the game is:
        - installed (local games list appended in _check_installed)
        - uninstalled (exe no longer exists)
        - launched (via Galaxy - pid tracking started)
        - stopped (process no longer running/is zombie)
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
        self._settings.reload_config_if_changed()

        if self._owned_check.done() and self._settings.library.has_changed():
            self._owned_check = asyncio.create_task(self._check_owned())

        if self._settings.installed.has_changed():
            self._rescan_needed = True

        if self._installed_check.done():
            self._installed_check = asyncio.create_task(self._check_installed())

        if self._statuses_check.done():
            self._statuses_check = asyncio.create_task(self._check_statuses())

    async def shutdown(self):
        self._owned_check.cancel()
        self._statuses_check.cancel()
        self._installed_check.cancel()
        await self._api.close_session()


def main():
    setup_sentry()
    create_and_run_plugin(HumbleBundlePlugin, sys.argv)

if __name__ == "__main__":
    main()
