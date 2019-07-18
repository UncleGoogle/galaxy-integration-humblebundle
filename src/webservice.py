from http.cookies import SimpleCookie
import aiohttp
import json
import base64
import logging

from galaxy.http import create_client_session


class AuthorizedHumbleAPI:
    _PROCESS_LOGIN = "https://www.humblebundle.com/processlogin"
    _ORDER_LIST_URL = "https://www.humblebundle.com/api/v1/user/order"
    _ORDER_URL = "https://www.humblebundle.com/api/v1/order/{}"
    _DEFAULT_PARAMS = {"ajax": "true"}
    _DEFAULT_HEADERS = {
        "Accept": "application/json",
        "Accept-Charset": "utf-8",
        "Keep-Alive": "true",
        "X-Requested-By": "hb_android_app",
        "User-Agent": "Apache-HttpClient/UNAVAILABLE (java 1.4)"
    }
    def __init__(self):
        self._simpleauth_sess = None
        self._session = create_client_session(headers=self._DEFAULT_HEADERS)

    async def _request(self, *args, **kwargs):
        if 'params' not in kwargs:
            kwargs['params'] = self._DEFAULT_PARAMS
        return await self._session.request(*args, **kwargs)

    def _decode_user_id(self, _simpleauth_sess):
        info = _simpleauth_sess.split('|')[0]
        # get rid of escape characters
        info = bytes(info, "utf-8").decode("unicode_escape")
        info_padded = info + '=='
        decoded = json.loads(base64.b64decode(info_padded))
        logging.debug(decoded)
        return decoded['user_id']

    async def authenticate(self, auth_cookie: dict):
        cookie = SimpleCookie()
        cookie[auth_cookie['name']] = auth_cookie['value']
        self._session.cookie_jar.update_cookies(cookie)
        user_id = self._decode_user_id(auth_cookie['value'])
        return (user_id, user_id)

    async def get_gamekeys(self):
        res = await self._request('get', self._ORDER_LIST_URL)
        parsed = await res.json()
        logging.info(f"The order list:\n{parsed}")
        gamekeys = [it["gamekey"] for it in parsed]
        return gamekeys

    async def get_order_details(self, gamekey):
        res = await self._request('get', self._ORDER_URL.format(gamekey))
        return await res.json()





