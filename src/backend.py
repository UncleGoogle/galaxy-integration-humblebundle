from http.cookies import SimpleCookie
import aiohttp
import json
import base64
import logging

from galaxy.http import create_client_session

PROCESS_LOGIN = "https://www.humblebundle.com/processlogin"
ORDER_LIST_URL = "https://www.humblebundle.com/api/v1/user/order"
ORDER_URL = "https://www.humblebundle.com/api/v1/order/{order_id}"


class Backend:
    _default_params = {"ajax": "true"}
    _default_headers = {
        "Accept": "application/json",
        "Accept-Charset": "utf-8",
        "Keep-Alive": "true",
        "X-Requested-By": "hb_android_app",
        "User-Agent": "Apache-HttpClient/UNAVAILABLE (java 1.4)"
    }
    def __init__(self):
        self._simpleauth_sess = None
        self._session = create_client_session(headers=self._default_headers)

    async def authenticate(self, auth_cookie: dict):
        cookie = SimpleCookie()
        cookie[auth_cookie['name']] = auth_cookie['value']
        self._session.cookie_jar.update_cookies(cookie)
        user_id = self.decode_user_id(auth_cookie['value'])
        return (user_id, user_id)

    async def _request(*args, **kwargs):
        if 'params' not in kwargs:
            kwargs['params'] = self._default_params
        return await self._session.request(*args, **kwargs)

    def decode_user_id(self, _simpleauth_sess):
        info = _simpleauth_sess.split('|')[0]
        info_padded = info + '=='
        decoded = json.loads(base64.b64decode(info_padded))
        logging.debug(decoded)
        return decoded['user_id']

    async def get_orders_list(self):
        res = await self._session.request('get',
            'https://www.humblebundle.com/api/v1/user/order?ajax=true')
        return res.json()

    async def get_order_details(self, gamekey):
        res = await self._session.request('get',
            f'https://www.humblebundle.com/api/v1/order/{gamekey}?all_tpkds=true')
        return res.json()





