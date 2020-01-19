import logging
import pathlib
import webbrowser
from functools import partial
from typing import Optional

import toga
from toga.style import Pack
from toga.style.pack import COLUMN


from gui.baseapp import BaseApp
# Imports from base level (sys.path is extended with the file parent)
# Yes, I know it's bad practise but it is not reusable package, only local code organiser
from settings import Settings
from consts import SOURCE


logger = logging.getLogger(__name__)


class Options(BaseApp):
    NAME = 'Galaxy HumbleBundle - Options'
    SIZE = (400, 300)

    def __init__(self):
        self._cfg = Settings()
        super().__init__(self.NAME, self.SIZE, has_menu=False)

    def on_source_switch(self, el):
        logger.info(f'Setting {el.label} {el.is_on}')
        val = SOURCE(el.label)
        if el.is_on:
            self._cfg.library.sources.add(val)
        else:
            self._cfg.library.sources.remove(val)
        if val == SOURCE.KEYS:
            self.show_revealed_sw.enabled = el.is_on
        self._cfg.save_config()

    def on_revealed_switch(self, el):
        logger.info(f'Swiching {el.label} {el.is_on}')
        self._cfg.library.show_revealed_keys = el.is_on
        self._cfg.save_config()

    def select_path(self, el, _):
        logger.debug(el, _)
        paths = self.main_window.select_folder_dialog('Chose humblebundle directory', multiselect=True)
        for path in paths:
            lbl = toga.Label(path)
            lbl.style.flex = 1
            lbl.style.width = 400
            logger.debug(f'adding {lbl} to {el}')
            el.add(lbl)
        el.refresh()

    def startup_method(self):
        # main container
        box = toga.Box(id='main_box')
        box.style.direction = 'column'
        box.style.padding = 15

        # library section
        self.show_revealed_sw = toga.Switch(
            'show_revealed_keys',
            on_toggle=self.on_revealed_switch, 
            is_on=self._cfg.library.show_revealed_keys,
            enabled=SOURCE.KEYS in self._cfg.library.sources,
            style=Pack(padding_left=20, padding_top=2)
        )
        sources_sw = [
            toga.Switch(s.value,on_toggle=self.on_source_switch, is_on=(s in self._cfg.library.sources))
            for s in SOURCE
        ] + [self.show_revealed_sw]

        lib_box = toga.Box(id='lib_box', children=sources_sw)
        lib_box.style.direction = 'column'

        box.add(lib_box)

        # # local games section
        # paths_box = toga.Box()
        # paths_box.style.direction = 'column'
        # paths_box.style.height = 400
        # paths_box.style.padding = 400
        # paths_box.add(toga.Label('Paths:'))

        # down_containter = toga.ScrollContainer(horizontal=False, content=paths_box)
        # box.add(down_containter)

        # container = toga.OptionContainer() 
        # config_box = toga.Box(children=library_opts + [paths_box, select_btn])
        # about_box = toga.Box()
        # container.add('Config', config_box)
        # container.add('About', about_box)
        # box.add(container)

        # select_btn = toga.Button('Select path', on_press=partial(self.select_path, paths_box))
        # box.add(select_btn)

        return box


if __name__ == '__main__':
    Options().main_loop()