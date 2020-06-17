import logging
import pathlib
import enum
from typing import Optional

import toga
from toga.style import Pack

from gui.baseapp import BaseApp
from gui.toga_helpers import set_tooltip, LinkLabel, OneColumnTable, OptionContainer

from settings import Settings
from consts import SOURCE, IS_MAC, IS_WINDOWS


logger = logging.getLogger(__name__)


class OPTIONS_MODE(enum.Enum):
    NORMAL = 'normal'
    WELCOME = 'welcome'
    NEWS = 'news'


class Options(BaseApp):
    NAME = 'Galaxy HumbleBundle Options'
    if IS_WINDOWS:
        SIZE = (620, 255)
        TEXT_SIZE = 9
        TEXT_SIZE_BIG = 10
    elif IS_MAC:
        SIZE = (620, 340)
        TEXT_SIZE = 11
        TEXT_SIZE_BIG = 12

    def __init__(self, mode: OPTIONS_MODE, changelog_path: pathlib.Path):
        self._mode = mode
        self._changelog_path = changelog_path
        self._cfg = Settings(suppress_initial_change=True)
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
        desc = "Choose HumbleBundle game types to be shown in your GOG Galaxy library.\n" \
               "Subscription games settings are placed in Galaxy Settings->Features"
        source_help = {
            SOURCE.DRM_FREE: "Games from www.humblebundle.com/home/library that have direct download for Windows, Mac or Linux",
            SOURCE.KEYS: "Game keys to be redeemed in foreign services like Steam or Origin."
        }
        show_revealed_help = 'Check to show all game keys as separate games.\n' \
            'Uncheck to show only game keys that are already revealed\n' \
            '(redeemed keys are usually reported by other Galaxy plugins).'

        description = toga.Label(desc, style=Pack(font_size=self.TEXT_SIZE_BIG, padding_bottom=12))
        rows = [description]
        self.show_revealed_sw = toga.Switch(
            'show_revealed_keys',
            on_toggle=self._on_revealed_switch,
            is_on=self._cfg.library.show_revealed_keys,
            enabled=SOURCE.KEYS in self._cfg.library.sources,
            style=Pack(padding_left=20, padding_top=2)
        )
        for s in SOURCE:
            sw = toga.Switch(s.value, on_toggle=self._on_source_switch, is_on=(s in self._cfg.library.sources))
            sw.style.padding_bottom = 2
            set_tooltip(sw, source_help[s])
            rows.append(sw)
        set_tooltip(self.show_revealed_sw, show_revealed_help)
        rows.append(self.show_revealed_sw)

        if IS_MAC:  # workaround for not working tooltip
            inp = toga.MultilineTextInput(readonly=True, style=Pack(padding_top=10))
            inp.MIN_WIDTH = self.SIZE[0] - 50
            for k, v in source_help.items():
                inp.value += f'{k.value}: {v}\n'
            inp.value += f'show_revealed_help: {show_revealed_help}'
            rows.append(inp)

        lib_box = toga.Box(children=rows)
        lib_box.style.direction = 'column'
        lib_box.style.padding_bottom = 15
        return lib_box

    def _installed_section(self) -> toga.Widget:
        desc = "Choose directories for installed games lookup. The lookup is based on child directory names."
        description = toga.Label(desc, style=Pack(font_size=self.TEXT_SIZE_BIG, padding_bottom=12))
        if IS_MAC:
            desc_os = "If nothing selected, '/Applications' will be used."
        if IS_WINDOWS:
            desc_os = "e.g. 'C:/Humble' to detect 'C:/Humble/Torchlight/torch.exe' ('Torchlight' matches game name)."
        description_os = toga.Label(desc_os, style=Pack(font_size=self.TEXT_SIZE_BIG, padding_bottom=12))

        self._paths_table = OneColumnTable('Path', data=[str(p) for p in self._cfg.installed.search_dirs])

        select_btn = toga.Button('Add path', on_press=self._add_path)
        select_btn.style.flex = 1
        select_btn.style.padding_bottom = 4
        self._remove_btn = toga.Button('Remove path', on_press=self._remove_paths, enabled=self._paths_table.not_empty)
        self._remove_btn.style.flex = 1
        config_panel = toga.Box(children=[select_btn, self._remove_btn])
        config_panel.style.direction = 'row'
        config_panel.style.padding_top = 15

        paths_container = toga.Box(children=[description, description_os, self._paths_table, config_panel])
        paths_container.style.direction = 'column'
        return paths_container

    def _about_section(self) -> toga.Widget:
        lbl_style = Pack(font_size=self.TEXT_SIZE_BIG, text_align="center", padding_bottom=3)
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

    def _news_section(self) -> toga.Widget:
        margin = 15
        box = toga.Box()
        box.style.padding_bottom = margin

        try:
            with open(self._changelog_path, 'r') as f:
                changelog = f.read()
        except FileNotFoundError as e:
            changelog = str(e)
        text_box = toga.MultilineTextInput(readonly=True)
        text_box.MIN_WIDTH = self.SIZE[0] - (2 * margin)
        text_box.MIN_HEIGHT = self.SIZE[1] - (2 * margin)
        text_box.value = changelog

        box.add(text_box)
        return box

    def startup_method(self) -> toga.Widget:
        main_container = OptionContainer()

        sections = {
            'Library': self._library_section,
            'Installed': self._installed_section,
            'Changelog': self._news_section,
            'About': self._about_section
        }
        for name, create_tab_content in sections.items():
            section = toga.Box()
            section.style.padding = 15
            section.add(create_tab_content())
            main_container.add(name, section)

        if self._mode in [OPTIONS_MODE.WELCOME, OPTIONS_MODE.NORMAL]:
            main_container.open_tab(0)
        if self._mode == OPTIONS_MODE.NEWS:
            main_container.open_tab(2)

        return main_container
