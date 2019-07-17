import sys
import os
import json
import logging
import re

from galaxy.api.plugin import Plugin, create_and_run_plugin
from galaxy.api.consts import Platform
from galaxy.api.types import Authentication, NextStep
from galaxy.api.errors import InvalidCredentials

from version import __version__
from backend import Backend


AUTH_PARAMS = {
    "window_title": "Login to HumbleBundle",
    "window_width": 560,
    "window_height": 610,
    "start_uri": "https://www.humblebundle.com/login?goto=/home/library",  # or https://www.humblebundle.com/account-start?goto=home"
    "end_uri_regex": "^" + re.escape("https://www.humblebundle.com/home/library")
}


class HumbleBundlePlugin(Plugin):
    def __init__(self, reader, writer, token):
        super().__init__(Platform.HumbleBundle, __version__, reader, writer, token)
        self._backend = Backend()

    async def authenticate(self, stored_credentials=None):
        if not stored_credentials:
            return NextStep("web_session", AUTH_PARAMS)

        logging.info('stored credentials found')
        user_id, user_name = await self._backend.authenticate(stored_credentials)
        return Authentication(user_id, user_name)

    async def pass_login_credentials(self, step, credentials, cookies):
        logging.info(json.dumps(cookies, indent=4))
        auth_cookie = next(filter(lambda c: c['name'] == '_simpleauth_sess', cookies))
        logging.debug(f'===auth cookie, type {type(auth_cookie)}, val: {auth_cookie}')
        self.store_credentials(auth_cookie)

        user_id, user_name = await self._backend.authenticate(auth_cookie)
        return Authentication(user_id, user_name)

    async def get_owned_games(self):
        orders = await self._backend.get_orders_list()
        log.info(orders)
        return []

    def shutdown(self):
        self._backend._session.close()

def main():
    create_and_run_plugin(HumbleBundlePlugin, sys.argv)

if __name__ == "__main__":
    main()

