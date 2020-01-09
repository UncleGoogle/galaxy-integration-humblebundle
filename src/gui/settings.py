import pathlib
import webbrowser
from typing import Optional

from gui._base import BaseApp
import toga


class Options(BaseApp):
    NAME = 'Galaxy HumbleBundle – Options'
    SIZE = (640, 400)

    def __init__(self):
        super().__init__(self.NAME, self.SIZE, has_menu=False)

    def startup_method(self):
        box = toga.Box()
        return box
