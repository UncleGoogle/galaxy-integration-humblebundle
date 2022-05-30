from http.cookies import SimpleCookie
from http import HTTPStatus
from contextlib import contextmanager
import typing as t
import aiohttp
import json
import base64
import logging

import yarl
import galaxy.http
from galaxy.api.errors import UnknownBackendResponse, AuthenticationRequired

from model.download import  DownloadStructItem
from model.subscription import MontlyContentData, ChoiceContentData, ChoiceMonth


logger = logging.getLogger(__name__)


@contextmanager
def handle_exception():
    """Wrapper over galaxy.http to log error details"""
    with galaxy.http.handle_exception():
        try:
            yield
        except Exception as e:
            logger.error(e)
            raise


class WebpackParseError(UnknownBackendResponse):
    pass


class AuthorizedHumbleAPI:
    _AUTHORITY = "https://www.humblebundle.com/"
    _PROCESS_LOGIN = "processlogin"
    _ORDER_LIST_URL = "api/v1/user/order"
    _ORDER_URL = "/api/v1/order/{}"
    _ORDERS_BULK_URL = "api/v1/orders"

    TROVES_PER_CHUNK = 20
    _MAIN_PAGE = ""
    _SUBSCRIPTION = 'membership'
    _SUBSCRIPTION_HOME = 'membership/home'
    _SUBSCRIPTION_PRODUCTS = 'api/v1/subscriptions/humble_monthly/subscription_products_with_gamekeys'
    _SUBSCRIPTION_HISTORY = 'api/v1/subscriptions/humble_monthly/history?from_product={}'
    _DOWNLOAD_SIGN = 'api/v1/user/download/sign'
    _HUMBLER_REDEEM_DOWNLOAD = 'humbler/redeemdownload'

    _DEFAULT_HEADERS = {
        "Accept": "application/json",
        "Accept-Charset": "utf-8",
        "Keep-Alive": "true",
    }

    def __init__(self, headers: t.Dict[str, t.Any]):
        headers={**self._DEFAULT_HEADERS, **headers}
        self._session = galaxy.http.create_client_session(headers=headers)

    @property
    def is_authenticated(self) -> bool:
        return bool(self._session.cookie_jar)

    async def _request(self, method, path, *args, **kwargs):
        url = self._AUTHORITY + path
        logger.debug(f'{method}, {url}, {args}, {kwargs}')
        with handle_exception():
            return await self._session.request(method, url, *args, **kwargs)

    async def _validate_authentication(self) -> None:
        """Raises galaxy.api.errors.AuthenticationRequired when session got invalidated."""
        with handle_exception():
            response = await self._request('get', self._ORDER_LIST_URL, raise_for_status=False)
            if response.status in (401, 403):
                raise AuthenticationRequired()
            response.raise_for_status()

    def _decode_user_id(self, _simpleauth_sess) -> str:
        info = _simpleauth_sess.split('|')[0]
        info += '=='  # ensure full padding
        decoded = json.loads(base64.b64decode(info))
        return decoded['user_id']

    async def authenticate(self, auth_cookie: dict) -> str:
        # recreate original cookie
        cookie = SimpleCookie()
        cookie_val = bytes(auth_cookie['value'], "utf-8").decode("unicode_escape")
        # some users have cookies with escaped characters, some not...
        # for the first group strip quotes:
        cookie_val = cookie_val.replace('"', '')
        cookie[auth_cookie['name']] = cookie_val

        self._session.cookie_jar.update_cookies(cookie)
        await self._validate_authentication()
        return self._decode_user_id(cookie_val)

    async def get_gamekeys(self) -> t.List[str]:
        res = await self._request('get', self._ORDER_LIST_URL)
        parsed = await res.json()
        logger.info(f"The order list:\n{parsed}")
        gamekeys = [it["gamekey"] for it in parsed]
        return gamekeys

    async def get_order_details(self, gamekey) -> dict:
        res = await self._request('get', self._ORDER_URL.format(gamekey), params={
            'all_tpkds': 'true'
        })
        return await res.json()
    
    async def get_orders_bulk_details(self, gamekeys: t.Iterable) -> t.Dict[str, dict]:
        params = [('all_tpkds', 'true')] + [('gamekeys', gk) for gk in gamekeys]
        res = await self._request('get', self._ORDERS_BULK_URL, params=params)
        return await res.json()

    async def get_subscription_products_with_gamekeys(self) -> t.AsyncGenerator[dict, None]:
        """
        Yields list of subscription products - historically backward info
        for Humble Choice proceeded by Humble Monthly. Used by HumbleBundle in 
        `https://www.humblebundle.com/membership/home`

        Every product includes only A FEW representative games from given subscription and other data.
        For Choice: `gamekey` field presence means user has unlocked that month to make choices;
        `contentChoicesMade` field contain chosen games grouped by keys from "unlockedContentEvents".
        For Monthly: `download_url` field presence means user has subscribed this month.

        Yields list of products - historically backward subscriptions info.
        Choice products are in form of:
        {
            "contentChoiceData": {
                "initial": {...},  # includes only 4 `ContentChoice`s
                "extras": [...]
            },
            "gamekey": "wqheRstssFcHGcfP",  # when the month is unlocked already
            "isActiveContent": false,       # is current month
            "title": "May 2020",
            "MAX_CHOICES": 9,               # dropped after 05.2022
            "productUrlPath": "may-2020",
            "includesAnyUplayTpkds": false,
            "unlockedContentEvents": [
                "initial",
                "chessultra"
            ],
            "downloadPageUrl": "/downloads?key=wqheRstssFcHGcfP",  # unlocked month
            "contentChoicesMade": {
                "initial": {
                    "choices_made": [
                        "chessultra"
                    ]
                }
            },
            "usesChoices": true
            "canRedeemGames": true,
            "productMachineName": "may_2020_choice"
        }

        Monthly products goes after all choices and are in form of:
        {
            "machine_name": "september_2019_monthly",
            "highlights": [
                "8 Games",
                "$179.00 Value"
            ],
            "order_url": "/downloads?key=Ge882ERvybmawmWd",
            "short_human_name": "September 2019",
            "hero_image": "https://hb.imgix.net/a25aa69d4c827d42142d631a716b3fbd89c15733.jpg?auto=compress,format&fit=crop&h=600&w=1200&s=789fedc066299f3d3ed802f6f1e55b6f",
            "early_unlock_string": "Slay the Spire and Squad (Early Access)"
        }
        """
        cursor = ''
        while True:
            res = await self._request('GET', self._SUBSCRIPTION_PRODUCTS + f"/{cursor}", raise_for_status=False)
            if res.status == 404:  # Ends with "Humble Monthly" in November 2015
                return
            with handle_exception():
                res.raise_for_status()
            res_json = await res.json()
            for product in res_json['products']:
                yield product
            cursor = res_json['cursor']

    async def get_subscription_history(self, from_product: str) -> aiohttp.ClientResponse:
        """
        Marketing data of previous subscription months.
        :param from_product: machine_name of subscription following requested months
        for example 'february_2020_choice' to got a few month data items including
        'january_2020_choice', 'december_2019_choice', 'december_2020_monthly'
        """
        return await self._request('GET', self._SUBSCRIPTION_HISTORY.format(from_product), raise_for_status=False)

    async def get_previous_subscription_months(self, from_product: str):
        """Generator wrapper for get_subscription_history previous months"""
        while True:
            res = await self.get_subscription_history(from_product)
            if res.status == 404:
                return
            with handle_exception():
                res.raise_for_status()
            data = await res.json()
            if not data['previous_months']:
                return
            for prev_month in data['previous_months']:
                yield ChoiceMonth(prev_month)
            from_product = prev_month['machine_name']

    async def _get_webpack_data(self, path: str, webpack_id: str) -> dict:
        res = await self._request('GET', path)
        txt = await res.text()
        search = f'<script id="{webpack_id}" type="application/json">'
        json_start = txt.find(search) + len(search)
        candidate = txt[json_start:].strip()
        try:
            parsed, _ = json.JSONDecoder().raw_decode(candidate)
            return parsed
        except json.JSONDecodeError as e:
            raise WebpackParseError() from e
    
    async def get_user_subscription_state(self) -> dict:
        """
        for not subscriber:
        {"newestOwnedTier": null, "nextBilledPlan": "", "consecutiveContentDropCount": 0, "canResubscribe": false, "currentlySkippingContentHumanName": null, "perksStatus": "inactive", "billDate": "2021-11-30T18:00:00", "monthlyNewestOwnedContentMachineName": null, "willReceiveFutureMonths": false, "monthlyOwnsActiveContent": false, "unpauseDt": "2021-12-07T18:00:00", "creditsRemaining": 0, "currentlySkippingContentMachineName": null, "canBeConvertedFromGiftSubToPayingSub": false, "lastSkippedContentMachineName": null, "contentEndDateAfterBillDate": "2021-12-07T18:00:00", "isPaused": false, "monthlyNewestOwnedContentGamekey": null, "failedBillingMonths": 0, "wasPaused": false, "monthlyPurchasedAnyContent": false, "monthlyNewestOwnedContentEnd": null, "monthlyOwnsAnyContent": false, "monthlyNewestSkippedContentEnd": null}
        ---
        for subscriber with not unlocked active content:
        {"newestOwnedTier": "basic", "nextBilledPlan": "monthly_v2_basic", "consecutiveContentDropCount": 12, "canResubscribe": false, "currentlySkippingContentHumanName": null, "perksStatus": "active", "billDate": "2021-11-30T18:00:00", "monthlyNewestOwnedContentMachineName": "october_2021_choice", "willReceiveFutureMonths": true, "monthlyOwnsActiveContent": false, "unpauseDt": "2021-12-07T18:00:00", "creditsRemaining": 0, "currentlySkippingContentMachineName": null, "canBeConvertedFromGiftSubToPayingSub": false, "lastSkippedContentMachineName": "january_2021_choice", "contentEndDateAfterBillDate": "2021-12-07T18:00:00", "isPaused": false, "monthlyNewestOwnedContentGamekey": "***", "failedBillingMonths": 0, "monthlyNewestSkippedContentEnd": "2021-02-05T18:00:00", "wasPaused": false, "monthlyPurchasedAnyContent": true, "monthlyNewestOwnedContentEnd": "2021-11-02T17:00:00", "monthlyOwnsAnyContent": true)}
        ---
        at the time of creating this method, this data is attached to every humble page
        {}
        ---
        for subscriber at 2022-03:
        {"newestOwnedTier": "premium", "nextBilledPlan": "monthly_v2_premium", "consecutiveContentDropCount": 1, "canResubscribe": false, "currentlySkippingContentHumanName": null, "perksStatus": "active", "billDate": "2022-04-26T17:00:00", "monthlyNewestOwnedContentMachineName": "march_2022_choice", "willReceiveFutureMonths": true, "monthlyOwnsActiveContent": true, "unpauseDt": "2022-05-03T17:00:00", "creditsRemaining": 0, "currentlySkippingContentMachineName": null, "canBeConvertedFromGiftSubToPayingSub": false, "lastSkippedContentMachineName": null, "contentEndDateAfterBillDate": "2022-05-03T17:00:00", "isPaused": false, "monthlyNewestOwnedContentGamekey": "***", "failedBillingMonths": 0, "monthlyNewestSkippedContentEnd": null, "wasPaused": false, "monthlyPurchasedAnyContent": true, "monthlyNewestOwnedContentEnd": "2022-04-05T17:00:00", "monthlyOwnsAnyContent": true}
        """
        return await self._get_window_models(self._MAIN_PAGE, "userSubscriptionState")
    
    async def _get_window_models(self, path: str, model_name: str) -> dict:
        res = await self._request('GET', path)
        txt = await res.text()
        search = f'window.models.{model_name} = '
        json_start = txt.find(search) + len(search)
        candidate = txt[json_start:].strip()
        try:
            parsed, _ = json.JSONDecoder().raw_decode(candidate)
            return parsed
        except json.JSONDecodeError as e:
            raise WebpackParseError() from e
        
    async def get_subscriber_hub_data(self) -> dict:
        """
        Raises `WebpackParseError` when user was never a subscriber
        """
        webpack_id = "webpack-subscriber-hub-data"
        try:
            return await self._get_webpack_data(self._SUBSCRIPTION_HOME, webpack_id)
        except WebpackParseError:
            logger.warning("Cannot get subscriber info: probably user has never been a subscriber")
            raise

    async def get_main_page_webpack_data(self) -> dict:
        webpack_id = "webpack-json-data"
        return await self._get_webpack_data(self._MAIN_PAGE, webpack_id)

    async def get_choice_marketing_data(self) -> dict:
        """Parsing ~155K and fast response from server"""
        webpack_id = "webpack-choice-marketing-data"
        return await self._get_webpack_data(self._SUBSCRIPTION, webpack_id)

    async def get_choice_content_data(self, product_url_path) -> ChoiceContentData:
        """Parsing ~220K
        product_url_path: last element of choice subscripiton url for example 'february-2020'
        """
        url = self._SUBSCRIPTION + '/' + product_url_path
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
            logger.error(repr(e) + '. Error ignored')
        return urls

    async def close_session(self):
        await self._session.close()
