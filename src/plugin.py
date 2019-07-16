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

import requests
import http.cookiejar
import http.cookies
import aiohttp.cookiejar
from http.cookies import Morsel, SimpleCookie

from galaxy.http import create_client_session

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
        res = await self.poc(stored_credentials)
        # user_id, user_name = await self._backend.authenticate(stored_credentials)
        # return Authentication(user_id, user_name)

    async def pass_login_credentials(self, step, credentials, cookies):
        logging.info(json.dumps(cookies, indent=4))

        with open(os.path.join(os.path.dirname(__file__), "cookies"), 'w') as f:
            json.dump(cookies, f, indent=4)
        
        for c in cookies:
            if c['name'] == '_simpleauth_sess':
                simple_auth = c['value']
        
        self.store_credentials(simple_auth)
        await self.poc(simple_auth)
        user_id, user_name = await self._backend.authenticate(cookie_dict)
        return Authentication(user_id, user_name)

    async def get_owned_games(self):
        return []
    
    async def poc(self, auth_sess_cookie):
        self.default_headers = {
            "Accept": "application/json",
            "Accept-Charset": "utf-8",
            "Keep-Alive": "true",
            "X-Requested-By": "hb_android_app",
            "User-Agent": "Apache-HttpClient/UNAVAILABLE (java 1.4)"
        }
        self.default_params = {"ajax": "true"}

        self.session = create_client_session(headers=self.default_headers)

        cookie = SimpleCookie()
        cookie['_simpleauth_sess'] = auth_sess_cookie['value']
        self.session.cookie_jar.update_cookies(cookie)

        ORDER_LIST_URL = "https://www.humblebundle.com/api/v1/user/order?ajax=true"
        response = await self.session.request("GET", ORDER_LIST_URL)
        j = await response.json()
        print(j)


def main():
    create_and_run_plugin(HumbleBundlePlugin, sys.argv)

if __name__ == "__main__":
    main()

