import sys
import time
import asyncio
import os
import json
import logging
import re
import webbrowser

from galaxy.api.plugin import Plugin, create_and_run_plugin
from galaxy.api.consts import Platform
from galaxy.api.types import Authentication, NextStep
from galaxy.api.errors import InvalidCredentials

from version import __version__
from webservice import AuthorizedHumbleAPI
from humblegame import HumbleGame, HumbleDownloader
from consts import PlatformNotSupported, GAME_PLATFORMS


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
        self._games = {}
        self._downloader = HumbleDownloader()

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

        def is_game(sub):
            default = False
            return next(filter(lambda x: x['platform'] in GAME_PLATFORMS, sub['downloads']), default)

        games = {}
        gamekeys = await self._api.get_gamekeys()
        requests = [self._api.get_order_details(x) for x in gamekeys]

        logging.info(f'Fetching info about {len(requests)} orders started...')
        all_games_details = await asyncio.gather(*requests)
        logging.info('Fetching info finished')

        for details in all_games_details:
            for sub in details['subproducts']:
                try:
                    if is_game(sub):
                        games[sub['machine_name']] = HumbleGame(sub)
                except Exception as e:
                    logging.error(f'Error while parsing subproduct {sub}: {repr(e)}')
                    continue

        self._games = games
        return [g.in_galaxy_format() for g in games.values()]

    async def install_game(self, game_id):
        game = self._games.get(game_id)
        if game is None:
            logging.error(f'Install game: game {game_id} not found')
            return

        try:
            url = self._downloader.find_best_url(game.downloads)
        except Exception as e:
            logging.exception(e)
        else:
            webbrowser.open(url['web'])

    # async def launch_game(self, game_id):
    #     pass

    # async def uninstall_game(self, game_id):
    #     pass


    def shutdown(self):
        self._api._session.close()

def main():
    create_and_run_plugin(HumbleBundlePlugin, sys.argv)

if __name__ == "__main__":
    main()

