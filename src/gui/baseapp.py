import pathlib
import abc
from typing import Tuple

import toga


class BaseApp(toga.App, abc.ABC):
    APP_ID = 'org.galaxy-hb.plugin'
    H_ICON = str(pathlib.Path(__file__).resolve().parent / 'static' / 'h_icon.png')

    def __init__(self,
        window_name: str,
        size: Tuple[int, int],
        *args,
        has_menu: bool=False,
        **kwargs
    ):
        self._app_size = size
        self._has_menu = has_menu
        super().__init__(window_name, self.APP_ID, icon=self.H_ICON)

    def startup(self):
        self.main_window = toga.MainWindow(title=self.name, factory=self.factory, size=self._app_size)
        self.main_window.content = self.startup_method()
        self.main_window.show()

    @abc.abstractmethod
    def startup_method(self) -> toga.Widget:
        """Implements startup method. Returns content object to be assign to self.main_window.content"""

    def _create_impl(self):
        """Overwritten to remove menubar based on self._hb_menu"""
        if self._has_menu:
            print('create impl')
            return super()._create_impl()
        else:
            factory_app = self.factory.App
            factory_app.create_menus = lambda _: None
            return factory_app(interface=self)
