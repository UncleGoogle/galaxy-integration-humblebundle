import logging
import pathlib
import webbrowser
from functools import partial
from typing import Optional

import toga
from toga.style import Pack
from toga.style.pack import COLUMN

from gui.baseapp import BaseApp
from settings import Settings
from consts import SOURCE


logger = logging.getLogger(__name__)


class Options(BaseApp):
    NAME = 'Galaxy HumbleBundle - Options'
    SIZE = (640, 400)

    def __init__(self):
        self._cfg = Settings()
        super().__init__(self.NAME, self.SIZE, has_menu=False)

    def startup_method(self):

        self.sources_sw = [
            toga.Switch(s.value, on_toggle=self.on_source_switch, is_on=(s in self._cfg.library.sources))
            for s in SOURCE
        ]
        toga.Switch('show_revealed_keys', on_toggle=self.on_revealed_switch, is_on=self._cfg.library.show_revealed_keys)

        box = toga.Box(id='box', style=Pack(direction=COLUMN, padding=10), children=sources_sw)
        return box

        # paths_box = toga.Box()
        # paths_box.style.direction = 'column'
        # paths_box.style.height = 400
        # paths_box.add(toga.Label('Paths:'))

        # select_btn = toga.Button('Select path', on_press=partial(self.select_path, paths_box))
        # box.add(select_btn)

        # down_containter = toga.ScrollContainer(horizontal=False, content=paths_box)
        # box.add(scroller)

        # container = toga.OptionContainer() 
        # config_box = toga.Box(children=library_opts + [paths_box, select_btn])
        # about_box = toga.Box()
        # container.add('Config', config_box)
        # container.add('About', about_box)
        # box.add(container)

        # return box

    def lib_option(self, el):
        if el.is_on:
            print(f'Setting {el.label} on')
            self._cfg.library.sources.add(SOURCE(el.label))
        else:
            print(f'Setting {el.label} off')
            self._cfg.library.sources.remove(SOURCE(el.label))
        self._cfg.save_config()
    

    def select_path(self, el, _):
        print(el, _)
        paths = self.main_window.select_folder_dialog('Chose humblebundle directory', multiselect=True)
        for path in paths:
            lbl = toga.Label(path)
            lbl.style.flex = 1
            lbl.style.width = 400
            print('adding', lbl, 'to', el)
            el.add(lbl)
        el.refresh()


if __name__ == '__main__':
    Options().main_loop()