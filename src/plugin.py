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
        #debug
        if not stored_credentials:
            stored_credentials = {}
            cookies_file = os.path.join(os.path.dirname(__file__), "cookies")
            if os.path.exists(cookies_file):
                with open(cookies_file, 'r') as f:
                    cookies = json.load(f)
                    for c in cookies:
                        stored_credentials[c['name']] = c
                    logging.debug(type(stored_credentials))
                    logging.debug(stored_credentials)

        if not stored_credentials:
            return NextStep("web_session", AUTH_PARAMS)

        logging.info('stored credentials found')
        user_id, user_name = await self._backend.authenticate(stored_credentials)
        return Authentication(user_id, user_name)

    async def pass_login_credentials(self, step, credentials, cookies):
        logging.info(json.dumps(cookies, indent=4))

        with open(os.path.join(os.path.dirname(__file__), "cookies"), 'w') as f:
            json.dump(cookies, f, indent=4)
        
        # cookies = json.loads(cookies)
        cookie_dict = {}
        for c in cookies:
            cookie_dict[c['name']] = c
            logging.debug(c)
            logging.debug(type(c))
            if c['name'] == '_simpleauth_sess':
                simple_auth = c['value']
        
        user_id, user_name = await self._backend.authenticate(cookie_dict)
        self.store_credentials(cookie_dict)
        return Authentication(user_id, user_name)

    async def get_owned_games(self):
        return []


def main():
    create_and_run_plugin(HumbleBundlePlugin, sys.argv)

if __name__ == "__main__":
    main()

