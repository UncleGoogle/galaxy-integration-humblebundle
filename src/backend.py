from galaxy.http import HttpClient


class Backend(HttpClient):
    def __init__(self):
        self._cookies = None

    async def authenticate(self, cookies):
        pass