import sys
import time
import asyncio
import os
import json
import logging
import re
import webbrowser

import sentry_sdk

from galaxy.api.plugin import Plugin, create_and_run_plugin
from galaxy.api.consts import Platform
from galaxy.api.types import Authentication, NextStep
from galaxy.api.errors import InvalidCredentials

from version import __version__
from consts import GAME_PLATFORMS, CURRENT_SYSTEM, HP
from webservice import AuthorizedHumbleAPI
from humblegame import TroveGame, Subproduct
from humbledownloader import HumbleDownloadResolver
from local import WindowsRegistryClient


sentry_sdk.init(
    "https://5b8ef07071c74c0a949169c1a8d41d1c@sentry.io/1514964",
    release=f"galaxy-integration-humblebundle@{__version__}"
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
        self._app_finder = WindowsRegistryClient() if CURRENT_SYSTEM == HP.WINDOWS else None
        self._owned_games = {}
        self._local_games = {}

    async def authenticate(self, stored_credentials=None):
        if not stored_credentials:
            return NextStep("web_session", AUTH_PARAMS)

        logging.info('stored credentials found')
        user_id, user_name = await self._api.authenticate(stored_credentials)
        return Authentication(user_id, user_name)

    async def pass_login_credentials(self, step, credentials, cookies):
        logging.debug(json.dumps(cookies, indent=2))
        auth_cookie = next(filter(lambda c: c['name'] == '_simpleauth_sess', cookies))

        user_id, user_name = await self._api.authenticate(auth_cookie)
        self.store_credentials(auth_cookie)
        return Authentication(user_id, user_name)

    async def get_owned_games(self):
        gamekeys = await self._api.get_gamekeys()
        orders = [self._api.get_order_details(x) for x in gamekeys]

        logging.info(f'Fetching info about {len(orders)} orders started...')
        all_games_details = await asyncio.gather(*orders)
        logging.info('Fetching info finished')

        products = []

        if await self._api.is_trove_subscribed():
            logging.info(f'Fetching trove info started...')
            troves = await self._api.get_trove_details()
            logging.info('Fetching info finished')
            for trove in troves:
                products.append(TroveGame(trove))

        for details in all_games_details:
            for sub in details['subproducts']:
                prod = Subproduct(sub)
                if not set(prod.downloads).isdisjoint(GAME_PLATFORMS):
                    # at least one download is for supported OS
                    products.append(prod)

        self._owned_games = {
            product.machine_name: product
            for product in products
        }

        return [g.in_galaxy_format() for g in self._owned_games.values()]

    async def get_local_games(self):
        if not self._app_finder:
            return []

        self._local_games.clear()
        for game in self._owned_games.values():
            if self._app_finder.is_app_installed(game.human_name):
                self._local_games[game.machine_name] = game

        return [g.in_galaxy_format() for g in self._local_games.values()]

    async def install_game(self, game_id):
        game = self._owned_games.get(game_id)
        if game is None:
            raise RuntimeError(f'Install game: game {game_id} not found')

        try:
            chosen_download = self._download_resolver(game)
        except Exception as e:
            logging.exception(e)
            raise

        if isinstance(game, TroveGame):
            url = await self._api.get_trove_sign_url(chosen_download, game.machine_name)
            webbrowser.open(url['signed_url'])
        else:
            webbrowser.open(chosen_download.web)

    # async def launch_game(self, game_id):
        

    # async def uninstall_game(self, game_id):
    #     game = self._local_games[game_id]
    #     if game is None:
    #         logging.error('game not found')
        
    def shutdown(self):
        self._api._session.close()

def main():
    create_and_run_plugin(HumbleBundlePlugin, sys.argv)

if __name__ == "__main__":
    main()

