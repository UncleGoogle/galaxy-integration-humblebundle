from http.cookies import SimpleCookie
import aiohttp
import json
import base64
import logging

from galaxy.http import create_client_session, handle_exception


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
        with handle_exception():
            if 'params' not in kwargs:
                kwargs['params'] = self._DEFAULT_PARAMS
            try:
                return await self._session.request(*args, **kwargs)
            except Exception as e:
                logging.error(repr(e))
                raise

    def _decode_user_id(self, _simpleauth_sess):
        info = _simpleauth_sess.split('|')[0]
        logging.debug(f'user info cookie: {info}')
        info += '=='  # ensure full padding
        decoded = json.loads(base64.b64decode(info))
        return decoded['user_id']

    async def authenticate(self, auth_cookie: dict):
        # recreate original cookie
        cookie = SimpleCookie()
        cookie_val = bytes(auth_cookie['value'], "utf-8").decode("unicode_escape")
        # some users have cookies with escaped characters, some not...
        # for the first group strip quotes:
        cookie_val = cookie_val.replace('"', '')
        cookie[auth_cookie['name']] = cookie_val

        user_id = self._decode_user_id(cookie_val)
        self._session.cookie_jar.update_cookies(cookie)

        # check if auth session is valid
        await self.get_gamekeys()

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





