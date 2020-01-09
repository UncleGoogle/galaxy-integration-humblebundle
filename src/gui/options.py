import pathlib
import webbrowser
from typing import Optional

from gui.baseapp import BaseApp
import toga

import logging


logger = logging.getLogger(__name__)


class Options(BaseApp):
    NAME = 'Galaxy HumbleBundle - Options'
    SIZE = (640, 400)

    def __init__(self):
        super().__init__(self.NAME, self.SIZE, has_menu=False)

    def startup_method(self):
        box = toga.Box()
        trove_sw = toga.Switch('trove', on_toggle=self.lib_option, is_on=True)
        box.add(trove_sw)
        return box

    def lib_option(self, val):
        logger.debug(val)
        print(val)

