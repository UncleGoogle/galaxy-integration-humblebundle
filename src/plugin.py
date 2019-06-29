import sys
import logging
import pathlib

root = pathlib.Path(__file__) / '..' / '..'
galaxy_api = root / 'galaxy-integrations-python-api' / 'src'
sys.path.append(str(galaxy_api.resolve()))

from galaxy.api.plugin import Plugin, create_and_run_plugin
from galaxy.api.consts import Platform
from galaxy.api.types import Authentication, NextStep

from version import __version__
from backend import Backend


class HumbleBundlePlugin(Plugin):
    def __init__(self, reader, writer, token):
        super().__init___(Platform.HumbleBundle, __version__, writer, reader, token)   
        self._backend = Backend()
    
    async def authenticate(self, stored_credentials=None):
        if stored_credentials:
            logging.info('stored credentials found')
            user = self._backend.auth_with_credentials()
            return Authentication(user.id, user.nickname)
        
        # TODO
        return NextStep()
        
        
        

        

            
