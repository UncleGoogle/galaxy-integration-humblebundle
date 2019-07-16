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
                        




    