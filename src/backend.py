from galaxy.http import create_client_session
import aiohttp
import json
import base64
import logging

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

    async def authenticate(self, cookies):
        self._session.cookie_jar.update_cookies(cookies)
        # for c in cookies:
        #     if c['name'] == '_simleauth_sess':
        #         user_id = self.decode_user_id(c['value'])
        #         break

        # headers = {
        #     'accept': 'application/json, text/javascript, */*; q=0.01',
        #     'accept-encoding': 'gzip, deflate, br',
        #     'accept-language': 'en-US,en;q=0.9,pl;q=0.8',
        #     'content-length': 565,
        #     'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        #     'cookie': 'csrf_cookie=IiqCNfEbQrT87Pue-1-1562014703; __ssid=10808b39cc6ab8b3d7698058c3d5d7f; _evidon_consent_cookie={"consent_date":"2019-07-01T21:01:37.198Z"}; _simpleauth_sess="eyJpZCI6IkI0ZWxTc2p0OGIifQ\075\075|1562742454|6399e0853d4b300eab843753155f295655a67d6c"; grecaptcha-v3-cookie=03AOLTBLQCRPePzd4w5ESqXMup-hy68C6FLTHNj9T1aZTy0E2dK8Ls3XJizEJdPV6al38KQo6NH3cd3ch72BjUjLvjlS6uxT5iG-9dI97LhnuN4idKzKrIcwT7ZSeQ2i2OoIL8WjvnZgs6VkLe14UAa6upu5xbsRJ58EaFLY2de1Q_9tNDUKO5ERJ-URP-FU5Z1iFzCUxpVAwTJtV7teZSvBqY5krTU4WCRDM3xxYNSwOznXL5QrJRnkh704-BYX39qv2LQ3jaNiwM4j-NiCaQnHeKiw9RqrC8Qhg1pYExWqVPyKSf5DMaMNCiz90Q_YJe2_x-fQgF7D6IJCf34eKZxP5isKPoTsjQf_7NBNGCxJBkabS7ldqcFUoE3hDLQzFn_yMjCfvqMTBgd7u39Uh-Fey5sHbRdEU8bg',
        #     'csrf-prevention-token': 'IiqCNfEbQrT87Pue-1-1562014703',
        #     'dnt': '1',
        #     'origin': 'https://www.humblebundle.com',
        #     'referer': 'https://www.humblebundle.com/login?goto=/home/library',
        #     'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
        #     'x-requested-with': 'XMLHttpRequest'
        # }
        try:
            response = await self._session.request('POST', PROCESS_LOGIN)
            logging.info(response.json())
        except Exception as e:
            logging.exception(e)
        # return response.json()
        return ('mock', 'mockname')
    
    def decode_user_id(self, _simpleauth_sess):
        info = _simpleauth_sess.split('|')[0]
        info_padded = info + '=='
        j = json.loads(base64.b64decode(info_padded))
        return j.user_id

    async def get_orders_list(self):
        res = self._session.request('get',
            'https://www.humblebundle.com/api/v1/user/order?ajax=true')
        return res.json()
    
    async def get_order_details(self, gamekey):
        res = self._session.request('get',
            f'https://www.humblebundle.com/api/v1/order/{gamekey}?all_tpkds=true')
        return res.json()
                        




    