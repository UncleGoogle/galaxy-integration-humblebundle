from http.cookies import SimpleCookie
from http import HTTPStatus
import typing as t
import aiohttp
import json
import base64
import logging

import yarl
from galaxy.http import create_client_session, handle_exception
from galaxy.api.errors import UnknownBackendResponse

from model.download import TroveDownload, DownloadStructItem
from model.subscription import MontlyContentData, ChoiceContentData, ContentChoiceOptions, ChoiceMarketingData, ChoiceMonth


class AuthorizedHumbleAPI:
    _AUTHORITY = "https://www.humblebundle.com/"
    _PROCESS_LOGIN = "processlogin"
    _ORDER_LIST_URL = "api/v1/user/order"
    _ORDER_URL = "/api/v1/order/{}"

    TROVES_PER_CHUNK = 20
    _SUBSCRIPTION = 'subscription'
    _SUBSCRIPTION_HOME = 'subscription/home'
    _SUBSCRIPTION_TROVE = 'subscription/trove'
    _SUBSCRIPTION_PRODUCTS = 'api/v1/subscriptions/humble_monthly/subscription_products_with_gamekeys'
    _SUBSCRIPTION_HISTORY = 'api/v1/subscriptions/humble_monthly/history?from_product={}'
    _TROVE_CHUNK_URL = 'api/v1/trove/chunk?property=popularity&direction=desc&index={}'
    _DOWNLOAD_SIGN = 'api/v1/user/download/sign'
    _HUMBLER_REDEEM_DOWNLOAD = 'humbler/redeemdownload'

    _DEFAULT_HEADERS = {
        "Accept": "application/json",
        "Accept-Charset": "utf-8",
        "Keep-Alive": "true",
        "User-Agent": "HumbleBundle plugin for GOG Galaxy 2.0"
    }

    def __init__(self):
        self._session = create_client_session(headers=self._DEFAULT_HEADERS)

    @property
    def is_authenticated(self) -> bool:
        return bool(self._session.cookie_jar)

    async def _request(self, method, path, *args, **kwargs):
        url = self._AUTHORITY + path
        logging.debug(f'{method}, {url}, {args}, {kwargs}')
        with handle_exception():
            return await self._session.request(method, url, *args, **kwargs)

    async def _is_session_valid(self):
        """Simply asks about order list to know if session is valid.
        galaxy.api.errors instances cannot be catched so galaxy.http.handle_excpetion
        is the final check with all the logic under its context.
        """
        with handle_exception():
            try:
                await self._session.request('get', self._AUTHORITY + self._ORDER_LIST_URL)
            except aiohttp.ClientResponseError as e:
                if e.status == HTTPStatus.UNAUTHORIZED:
                    return False
                raise
        return True

    def _decode_user_id(self, _simpleauth_sess):
        info = _simpleauth_sess.split('|')[0]
        info += '=='  # ensure full padding
        decoded = json.loads(base64.b64decode(info))
        return decoded['user_id']

    async def authenticate(self, auth_cookie: dict) -> t.Optional[str]:
        # recreate original cookie
        cookie = SimpleCookie()
        cookie_val = bytes(auth_cookie['value'], "utf-8").decode("unicode_escape")
        # some users have cookies with escaped characters, some not...
        # for the first group strip quotes:
        cookie_val = cookie_val.replace('"', '')
        cookie[auth_cookie['name']] = cookie_val

        self._session.cookie_jar.update_cookies(cookie)
        return self._decode_user_id(cookie_val)

    async def get_gamekeys(self) -> t.List[str]:
        res = await self._request('get', self._ORDER_LIST_URL)
        parsed = await res.json()
        logging.info(f"The order list:\n{parsed}")
        gamekeys = [it["gamekey"] for it in parsed]
        return gamekeys

    async def get_order_details(self, gamekey) -> dict:
        res = await self._request('get', self._ORDER_URL.format(gamekey), params={
            'all_tpkds': 'true'
        })
        return await res.json()

    async def _get_trove_details(self, chunk_index) -> list:
        res = await self._request('get', self._TROVE_CHUNK_URL.format(chunk_index))
        return await res.json()

    async def get_subscription_products_with_gamekeys(self):
        """
        Yields list of products - historically backward subscriptions info.
        Every product includes few representative games from given subscription and other data as:
        `ContentChoiceOptions` (with gamekey if unlocked and made choices)
        or `MontlyContentData` (with `download_url` if was subscribed this month)
        Used in `https://www.humblebundle.com/subscription/home`
        """
        cursor = ''
        while True:
            res = await self._request('GET', self._SUBSCRIPTION_PRODUCTS + f"/{cursor}")
            if res.status == 404:  # Ends in November 2015
                return
            res_json = await res.json()
            for product in res_json['products']:
                if 'isChoiceTier' in product:
                    try:
                        yield ContentChoiceOptions(product)
                    except KeyError as e:
                        logging.warning(repr(e))
                        continue  # ignore unexpected response without exiting generator
                else:  # no more choice content, now humble montly goes
                    # yield MontlyContentData(product)
                    return
            cursor = res_json['cursor']

    async def get_subscription_history(self, from_product: str):
        """
        Marketing data of previous subscription months.
        :param from_product: machine_name of subscription following requested months
        for example 'february_2020_choice' to got a few month data items including
        'january_2020_choice', 'december_2019_choice', 'december_2020_monthly'
        """
        res = await self._request('GET', self._SUBSCRIPTION_HISTORY.format(from_product))
        return await res.json()

    async def get_previous_subscription_months(self, from_product: str):
        """Generator wrapper for get_subscription_history previous months"""
        while True:
            res = await self.get_subscription_history(from_product)
            if res.status == 404:
                return
            for month in res['previous_months']:
                yield ChoiceMonth(month)
            from_product = month['machine_name']

    async def had_subscription(self) -> t.Optional[bool]:
        """Based on current behavior of `humblebundle.com/subscription/home`
        that is accesable only by "current and former subscribers"
        """
        res = await self._request('get', self._SUBSCRIPTION_HOME, allow_redirects=False)
        if res.status == 200:
            return True
        elif res.status == 302:
            return False
        else:
            logging.warning(f'{self._SUBSCRIPTION_HOME}, Status code: {res.status}')
            return None

    async def _get_webpack_data(self, path: str, webpack_id: str) -> dict:
        res = await self._request('GET', path)
        txt = await res.text()
        search = f'<script id="{webpack_id}" type="application/json">'
        json_start = txt.find(search) + len(search)
        candidate = txt[json_start:].strip()
        parsed, _ = json.JSONDecoder().raw_decode(candidate)
        return parsed

    async def get_montly_trove_data(self) -> dict:
        """Parses a subscription/trove page to find list of recently added games.
        Returns json containing "newlyAdded" trove games and "standardProducts" that is
        the same like output from api/v1/trove/chunk/index=0
        "standardProducts" may not contain "newlyAdded" sometimes
        """
        webpack_id = "webpack-monthly-trove-data"
        return await self._get_webpack_data(self._SUBSCRIPTION_TROVE, webpack_id)

    async def get_choice_marketing_data(self) -> ChoiceMarketingData:
        """Parsing ~155K and fast response from server"""
        webpack_id = "webpack-choice-marketing-data"
        data = await self._get_webpack_data(self._SUBSCRIPTION, webpack_id)
        return ChoiceMarketingData(data)

    async def get_choice_content_data(self, product_url_path) -> ChoiceContentData:
        """Parsing ~220K
        product_url_path: last element of choice subscripiton url for example 'february-2020'
        """
        url = 'subscription/' + product_url_path
        webpack_id = 'webpack-monthly-product-data'
        data = await self._get_webpack_data(url, webpack_id)
        return ChoiceContentData(data)

    async def get_montly_content_data(self, product_url_path) -> MontlyContentData:
        """
        product_url_path: last element of subscripiton url for example 'august_2019_monthly'
        """
        url = 'monthly/p/' + product_url_path
        webpack_id = 'webpack-monthly-product-data'
        data = await self._get_webpack_data(url, webpack_id)
        return MontlyContentData(data)

    async def get_trove_details(self, from_chunk: int=0):
        index = from_chunk
        while True:
            chunk_details = await self._get_trove_details(index)
            if type(chunk_details) != list:
                logging.debug(f'chunk_details: {chunk_details}')
                raise UnknownBackendResponse()
            elif len(chunk_details) == 0:
                logging.debug('No more chunk pages')
                return
            yield chunk_details
            index += 1

    async def sign_download(self, machine_name: str, filename: str):
        res = await self._request('post', self._DOWNLOAD_SIGN, params={
            'machine_name': machine_name,
            'filename': filename
        })
        return await res.json()

    async def _reedem_download(self, download_machine_name: str, custom_data: dict):
        """Unknown purpose - humble http client do this after post for signed_url
        Response should be text with {'success': True} if everything is OK
        """
        params = {
            'download': download_machine_name,
            'download_page': "false",  # TODO check what it does
        }
        params.update(custom_data)
        res = await self._request('post', self._HUMBLER_REDEEM_DOWNLOAD, params=params)
        content = await res.read()
        if content != b"{'success': True}":
            raise UnknownBackendResponse(f'unexpected response while reedem trove download: {content}')

    @staticmethod
    def _filename_from_web_link(link: str):
        return yarl.URL(link).parts[-1]

    async def sign_url_subproduct(self, download: DownloadStructItem, download_machine_name: str):
        if download.web is None:
            raise RuntimeError(f'No download web link in download struct item {download}')
        filename = self._filename_from_web_link(download.web)
        urls = await self.sign_download(download_machine_name, filename)
        try:
            await self._reedem_download(
                download_machine_name, {'download_url_file': filename})
        except Exception as e:
            logging.error(repr(e) + '. Error ignored')
        return urls

    async def sign_url_trove(self, download: TroveDownload, product_machine_name: str):
        if download.web is None:
            raise RuntimeError(f'No download web link in download struct item {download}')
        urls = await self.sign_download(download.machine_name, download.web)
        try:
            await self._reedem_download(
                download.machine_name, {'product': product_machine_name})
        except Exception as e:
            logging.error(repr(e) + '. Error ignored')
        return urls

    async def close_session(self):
        await self._session.close()
