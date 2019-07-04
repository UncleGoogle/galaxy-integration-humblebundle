import sys
import logging
import pathlib

from galaxy.api.plugin import Plugin, create_and_run_plugin
from galaxy.api.consts import Platform
from galaxy.api.types import Authentication, NextStep

from version import __version__
from backend import Backend


AUTH_PARAMS = {
    "window_title": "Login to HumbleBundle",
    "window_width": 480,
    "window_height": 800,
    "start_uri": "https://www.humblebundle.com/account-start?goto=home",
    # or: "https://www.humblebundle.com/login?goto=home"
    "end_uri_regex": "https://www.humblebundle.com/home/library"
}


class HumbleBundlePlugin(Plugin):
    def __init__(self, reader, writer, token):
        super().__init__(Platform.HumbleBundle, __version__, writer, reader, token)   
        self._backend = Backend()
    
    async def authenticate(self, stored_credentials=None):
        if not stored_credentials:
            return NextStep("web_session", AUTH_PARAMS)
        
        logging.info('stored credentials found')
        user = self._backend.auth_with_credentials(stored_credentials)
        return Authentication(user.id, user.nickname)
        
    async def pass_login_credentials(self, step, credentials, cookies):
        print(step, credentials, cookies)
        self._backend.authenticate(cookies)
        
        
        
def main():
    create_and_run_plugin(HumbleBundlePlugin, sys.argv)

if __name__ == "__main__":
    main()

        

            
