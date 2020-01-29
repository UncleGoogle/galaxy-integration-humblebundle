import logging
import pathlib
import webbrowser
from functools import partial
from typing import Optional

import toga
from toga.colors import rgb
from toga.style import Pack


from gui.baseapp import BaseApp
# Imports from base level (sys.path is extended with the file parent)
# Yes, I know it's bad practise but it is not reusable package, only code organiser
from settings import Settings
from consts import SOURCE, IS_WINDOWS, IS_MAC


logger = logging.getLogger(__name__)


# ---------- LinkLabel implementation -----------

if IS_WINDOWS:
    from toga_winforms.libs import WinForms
    from toga_winforms.widgets.label import Label as WinFormsLabel


    class WinformsLinkLabel(WinFormsLabel):
        def create(self):
            self.native = WinForms.LinkLabel()
            self.native.LinkClicked += WinForms.LinkLabelLinkClickedEventHandler(
                self.interface._link_clicked
            )

    
class LinkLabel(toga.Label):
    def __init__(self, text, link=None, id=None, style=None, factory=None):
        toga.Widget.__init__(self, id=id, style=style, factory=factory)

        if IS_WINDOWS:
            self._impl = WinformsLinkLabel(interface=self)
        elif IS_MAC:
            self._impl = self.factory.Label(interface=self)
            # no time for digging into cocoa NSTextField click handler
            # good enough workaournd for now
            self._impl.native.selectable = True

        self.link = link
        self.text = text
    
    @property
    def link(self):
        if self._link is None:
            return self.text
        return self._link
    
    @link.setter
    def link(self, link):
        self._link = link
    
    def _link_clicked(self, el, _):
        webbrowser.open(self.link)

# -----------------------------------------------


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
    def not_empty(self):
        return len(self.data) > 0
    
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
    NAME = 'Galaxy HumbleBundle Options'
    SIZE = (550, 250)

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
        if str(path) in [row.path for row in self._paths_table.data]:
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
            self._paths_table.data.append(path)
        self._remove_btn.enabled = self._paths_table.not_empty

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
        rows = self._paths_table.selection
        if rows is None:
            try:
                rows = [self._paths_table.data[-1]]
            except KeyError:
                logger.error('Removing when no data in table. Rm btn should be disabled at this point.')
                return
        for row in rows:
            self.__cfg_remove_path(row.path)
            self._paths_table.data.remove(row)
        self._remove_btn.enabled = self._paths_table.not_empty
    
    def _library_section(self) -> toga.Widget:
        self.show_revealed_sw = toga.Switch(
            'show_revealed_keys',
            on_toggle=self._on_revealed_switch, 
            is_on=self._cfg.library.show_revealed_keys,
            enabled=SOURCE.KEYS in self._cfg.library.sources,
            style=Pack(padding_left=20, padding_top=2)
        )
        sources_sw = [
            toga.Switch(s.value,on_toggle=self._on_source_switch, is_on=(s in self._cfg.library.sources))
            for s in SOURCE
        ]
        lib_box = toga.Box(children=sources_sw + [self.show_revealed_sw])
        lib_box.style.direction = 'column'
        lib_box.style.padding_bottom = 15
        return lib_box

    def _installed_section(self) -> toga.Widget:
        self._paths_table = OneColumnTable('Path', data=[str(p) for p in self._cfg.installed.search_dirs])

        select_btn = toga.Button('Add path', on_press=self._add_path)
        select_btn.style.flex = 1
        select_btn.style.padding_bottom = 4
        self._remove_btn = toga.Button('Remove', on_press=self._remove_paths, enabled=self._paths_table.not_empty)
        self._remove_btn.style.flex = 1

        left_panel = toga.Box(children=[select_btn, self._remove_btn])
        left_panel.style.direction = 'column'

        paths_container = toga.SplitContainer()
        paths_container.content = [left_panel, self._paths_table]
        paths_container.style.padding_bottom = 15
        return paths_container
    
    def _about_section(self) -> toga.Widget:
        lbl_style = Pack(font_size=10, text_align="center")
        labels = [
            toga.Label("Galaxy integration for HumbleBundle", style=lbl_style),
            LinkLabel("https://github.com/UncleGoogle/galaxy-integration-humblebundle", style=lbl_style),
            toga.Label("Copyright (C) 2019 UncleGoogle", style=lbl_style)
        ]
        
        box = toga.Box(children=labels)
        box.style.padding = (self.SIZE[1] // 4, self.SIZE[1] // 4)
        box.style.direction = 'column'
        box.style.alignment = 'center'
        return box

    def startup_method(self) -> toga.Widget:
        config_box = toga.Box()
        config_box.style.direction = 'column'
        config_box.style.padding = 15
        config_box.add(self._library_section())
        config_box.add(self._installed_section())

        about_box = toga.Box()
        about_box.style.padding = 15
        about_box.add(self._about_section())

        main_container = toga.OptionContainer() 
        main_container.add('Settings', config_box)
        main_container.add('About', about_box)

        return main_container


if __name__ == '__main__':
    Options().main_loop()