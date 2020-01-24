import logging
import pathlib
import webbrowser
from functools import partial
from typing import Optional

import toga
from toga.colors import rgb
from toga.style import Pack
# from toga.style.COLUMN import COLUMN


from gui.baseapp import BaseApp
# Imports from base level (sys.path is extended with the file parent)
# Yes, I know it's bad practise but it is not reusable package, only local code organiser
from settings import Settings
from consts import SOURCE, IS_WINDOWS


logger = logging.getLogger(__name__)


class OneColumnTable(toga.Table):
    """One column table"""
    def __init__(self, header: str, *args, **kwargs):
        super().__init__([header], *args, **kwargs)
        self.__set_full_width_one_column()

    def __set_full_width_one_column(self):
        if IS_WINDOWS:
            # winforms assumed: _iml.native is a ListView:
            # https://docs.microsoft.com/en-us/dotnet/api/system.windows.forms.listview?view=netframework-4.8
            width = self._impl.native.get_Width()
            # for some reason `width` is exactly half of the whole table
            self._impl.native.Columns[0].set_Width(width * 2)
    
    @property
    def selection(self):
        """Dummy addition for lacking toga implementation"""
        if IS_WINDOWS:  # winforms assumed
            idcs = self._impl.native.SelectedIndices
            selected_rows = []
            for i in idcs:
                selected_rows.append(self.data[i])
            if len(selected_rows) == 0:
                return None
            return selected_rows
        else:
            return super().selection


class Options(BaseApp):
    NAME = 'Galaxy HumbleBundle - Options'
    SIZE = (400, 300)

    def __init__(self):
        self._cfg = Settings()

        # dummy check to supress inital "change"
        self._cfg.library.has_changed()
        self._cfg.installed.has_changed()

        super().__init__(self.NAME, self.SIZE, has_menu=False)

    def _on_source_switch(self, el):
        logger.info(f'Setting {el.label} {el.is_on}')
        val = SOURCE(el.label)
        if el.is_on:
            self._cfg.library.sources.add(val)
        else:
            self._cfg.library.sources.remove(val)
        if val == SOURCE.KEYS:
            self.show_revealed_sw.enabled = el.is_on
        if self._cfg.library.has_changed():
            self._cfg.save_config()

    def _on_revealed_switch(self, el):
        logger.info(f'Swiching {el.label} {el.is_on}')
        self._cfg.library.show_revealed_keys = el.is_on
        if self._cfg.library.has_changed():
            self._cfg.save_config()
    
    def __cfg_add_path(self, raw_path: str) -> Optional[str]:
        """Adds path to config file and returns its normalized form"""
        path = pathlib.Path(raw_path).resolve()
        logger.info(f'Adding search_path {path}')
        if str(path) in [row.path for row in self.paths_table.data]:
            logger.info('Path already added. Skipping')
            return None
        self._cfg.installed.search_dirs.add(path)
        self._cfg.save_config()
        return str(path)

    def _add_path(self, el: toga.Button):
        try:
            paths = self.main_window.select_folder_dialog('Choose humblebundle directory', multiselect=True)
        except ValueError:
            logger.debug('No folder provided in the select folder dialog')
            return
        for raw_path in paths:
            path = self.__cfg_add_path(raw_path)
            if path is None:
                continue
            self.paths_table.data.append(path)
        self._remove_btn.enabled = bool(len(self.paths_table.data))

    def __cfg_remove_path(self, raw_path: str):
        path = pathlib.Path(raw_path).resolve()
        logger.info(f'Removing path {path}')
        try:
            self._cfg.installed.search_dirs.remove(path)
        except KeyError:  # should not happen; sanity check
            logger.error(f'Removing non existent path {path} from {self._cfg.installed.search_dirs}')
        else:
            self._cfg.save_config()

    def _remove_paths(self, _: toga.Button):
        rows = self.paths_table.selection
        if rows is None:
            try:
                rows = [self.paths_table.data[-1]]
            except KeyError:
                logger.error('Removing when no data in table. Rm btn should be disabled at this point.')
                return
        for row in rows:
            self.__cfg_remove_path(row.path)
            self.paths_table.data.remove(row)
        self._remove_btn.enabled = bool(len(self.paths_table.data))

    def startup_method(self):
        # main container
        box = toga.Box()
        box.style.direction = 'column'
        box.style.padding = 15

        # library section
        self.show_revealed_sw = toga.Switch(
            'show_revealed_keys',
            on_toggle=self._on_revealed_switch, 
            is_on=self._cfg.library.show_revealed_keys,
            enabled=SOURCE.KEYS in self._cfg.library.sources,
            style=Pack(padding_left=20, padding_top=2)
        )
        sources_sw = [
            toga.Switch(s.value, on_toggle=self._on_source_switch, is_on=(s in self._cfg.library.sources))
            for s in SOURCE
        ] + [self.show_revealed_sw]

        lib_box = toga.Box(id='lib_box', children=sources_sw)
        lib_box.style.direction = 'column'
        lib_box.style.flex = 1

        box.add(lib_box)

        # local games section
        paths_container = toga.SplitContainer()

        self.paths_table = OneColumnTable('Path', data=[str(p) for p in self._cfg.installed.search_dirs])
        if IS_WINDOWS:
            width = self.paths_table._impl.native.get_Width()
            self.paths_table._impl.native.Columns[0].set_Width(width * 2)

        select_btn = toga.Button('Add path', on_press=self._add_path)
        select_btn.style.flex = 1
        self._remove_btn = toga.Button('Remove', on_press=self._remove_paths, enabled=bool(len(self.paths_table.data)))
        select_btn.style.flex = 1

        left_panel = toga.Box(children=[select_btn, self._remove_btn])
        left_panel.style.direction = 'column'

        paths_container.content = [left_panel, self.paths_table]
        box.add(paths_container)

        # down_containter = toga.ScrollContainer(horizontal=False, content=paths_box)
        # box.add(down_containter)

        # # options containter
        # container = toga.OptionContainer() 
        # config_box = toga.Box(children=library_opts + [paths_box, select_btn])
        # about_box = toga.Box()
        # container.add('Config', config_box)
        # container.add('About', about_box)
        # box.add(container)

        return box


if __name__ == '__main__':
    Options().main_loop()