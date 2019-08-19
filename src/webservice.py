from http.cookies import SimpleCookie
import json
import base64
import logging

from galaxy.http import create_client_session, handle_exception
from galaxy.api.errors import UnknownBackendResponse, UnknownError

from humblegame import TroveDownload


class AuthorizedHumbleAPI:
    _AUTHORITY = "https://www.humblebundle.com/"
    _PROCESS_LOGIN = "processlogin"
    _ORDER_LIST_URL = "api/v1/user/order"
    _ORDER_URL = "/api/v1/order/{}"

    _TROVE_SUBSCRIBER = 'monthly/subscriber'
    _TROVE_CHUNK_URL = 'api/v1/trove/chunk?index={}'
    _TROVE_DOWNLOAD_SIGN_URL = 'api/v1/user/download/sign'
    _TROVE_REDEEM_DOWNLOAD = 'humbler/redeemdownload'

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

    async def _request(self, method, path, *args, **kwargs):
        url = self._AUTHORITY + path
        if 'params' not in kwargs:
            kwargs['params'] = self._DEFAULT_PARAMS
        with handle_exception():
            try:
                return await self._session.request(method, url, *args, **kwargs)
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

    async def _get_trove_details(self, chunk_index):
        res = await self._request('get', self._TROVE_CHUNK_URL.format(chunk_index))
        return await res.json()

    async def had_trove_subscription(self) -> bool:
        """Based on current behavior of `humblebundle.com/monthly/subscriber` that redirect to `monthly`
        if subscription was never enabled for the user.
        """
        res = await self._request('get', self._TROVE_SUBSCRIBER, allow_redirects=False)
        if res.status == 200:
            return True
        elif res.status == 302:
            return False
        else:
            logging.info(f'{self._TROVE_SUBSCRIBER}, Status code: {res.status_code}')
            return False

    async def get_trove_details(self):
        troves = []
        chunks = 10  # hardcoded for now, as don't know if empty array output is ensured/stable
        for index in range(chunks):
            chunk_details = await self._get_trove_details(index)
            if type(chunk_details) != list:
                logging.debug(f'chunk_details: {chunk_details}')
                raise UnknownBackendResponse()
            elif len(chunk_details) == 0:
                logging.debug('No more pages')
                break
            troves += chunk_details
        else:
            logging.warning(f'Index limit ({chunks}) for trove games reached!')
        return troves

    async def _get_trove_signed_url(self, download: TroveDownload):
        res = await self._request('post', self._TROVE_DOWNLOAD_SIGN_URL, params={
            'machine_name': download.machine_name,
            'filename': download.web
        })
        return await res.json()

    async def _reedem_trove_download(self, download: TroveDownload, product_machine_name: str):
        """Unknown purpose - humble http client do this after post for signed_url
        Response should be text with {'success': True} if everything is OK
        """
        res = await self._request('post', self._TROVE_REDEEM_DOWNLOAD, params={
            'download': download.machine_name,
            'download_page': "false",  # TODO check what it does
            'product': product_machine_name
        })
        content = await res.read()
        if content != b"{'success': True}":
            logging.error(f'unexpected response while reedem trove download: {content}')
            raise UnknownError()

    async def get_trove_sign_url(self, download: TroveDownload, product_machine_name: str):
        urls = await self._get_trove_signed_url(download)
        await self._reedem_trove_download(download, product_machine_name)
        return urls
