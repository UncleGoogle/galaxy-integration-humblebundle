import sys
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
        self._games = []
        self._downloader = HumbleDownloader()

    async def authenticate(self, stored_credentials=None):
        if not stored_credentials:
            return NextStep("web_session", AUTH_PARAMS)

        logging.info('stored credentials found')
        user_id, user_name = await self._api.authenticate(stored_credentials)
        return Authentication(user_id, user_name)

    async def pass_login_credentials(self, step, credentials, cookies):
        logging.info(json.dumps(cookies, indent=4))
        auth_cookie = next(filter(lambda c: c['name'] == '_simpleauth_sess', cookies))
        self.store_credentials(auth_cookie)

        user_id, user_name = await self._api.authenticate(auth_cookie)
        return Authentication(user_id, user_name)

    async def get_owned_games(self):

        def is_game(sub):
            default = False
            return next(filter(lambda x: x['platform'] in GAME_PLATFORMS, sub['downloads']), default)

        games = {}
        gamekeys = await self._api.get_gamekeys()
        for gamekey in gamekeys:
            details = await self._api.get_order_details(gamekey)
            logging.info(f'Parsing details of order {gamekey}:\n{json.dumps(details, indent=4)}')
            for sub in details['subproducts']:
                if is_game(sub):
                    games[sub['machine_name']] = HumbleGame(sub)

        self.games = games
        return [g.in_galaxy_format() for g in games.values()]

    async def install_game(self, game_id):
        game = self.games.get(game_id)
        if game is None:
            logging.error(f'Install game: game {game_id} not found')
            return

        try:
            url = self._downloader.find_best_url(game.downloads)
        except Exception as e:
            logging.exception(e)
        else:
            webbrowser.open(url['web'])


    def shutdown(self):
        self._api._session.close()

def main():
    create_and_run_plugin(HumbleBundlePlugin, sys.argv)

if __name__ == "__main__":
    main()

