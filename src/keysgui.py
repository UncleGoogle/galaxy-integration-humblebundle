import pathlib
import webbrowser
import sys
from typing import Optional

modules = pathlib.Path(__file__).parent / 'modules'
if modules.exists():
    sys.path.insert(0, str(modules))
else:  # FriendsOfGalaxy structure
    sys.path.insert(0, str(modules.parent))

import toga


class ShowKey(toga.App):
    WINDOW_NAME = 'Key'
    APP_ID = 'org.humblebundle-integration.key'
    KEYS_URL = 'https://www.humblebundle.com/home/keys'
    H_ICON = str(pathlib.Path(__file__).resolve().parent / 'static' / 'h_icon.png')

    def __init__(self, human_name: str, key_type: str, key_val: Optional[str]):
        self._key_type = key_type
        self._key_val = key_val
        revealed_info = ' (not revealed yet)' if self._key_val is None else ''
        self._info = f"{human_name}{revealed_info}:"

        super().__init__(f'{self._key_type} Key', self.APP_ID, icon=self.H_ICON)

    def startup(self):
        self.main_window = toga.MainWindow(title=self.name, factory=self.factory, size=(40, 40))

        box = toga.Box()
        info = toga.Label(self._info)
        info.style.padding = 10
        box.add(info)
        if self._key_val is None:
            el = toga.Button('Show keys in browser', on_press=self.open_keys_url)
        else:
            el = toga.TextInput(readonly=True, initial=self._key_val)
            el.style.width = 210

        el.style.padding = 30
        el.style.flex = 1
        box.add(el)

        self.main_window.content = box
        self.main_window.show()

    def open_keys_url(self, _):
        print('opening', self.KEYS_URL)
        webbrowser.open(self.KEYS_URL)

    def _create_impl(self):
        """Overwritten to remove menubar"""
        factory_app = self.factory.App
        factory_app.create_menus = lambda _: None
        return factory_app(interface=self)


def main():
    human_name = sys.argv[1]
    key_type = sys.argv[2]
    key_val = sys.argv[3]
    if key_val == 'None':
        key_val = None
    ShowKey(human_name, key_type, key_val).main_loop()


def test():
    key_data = {"machine_name": "jumbo_machinarium_steam", "key_type": "steam", "key_type_human_name": "Steam", "human_name": "Machinarium", "redeemed_key_val": "DXLVR-XXXXX-XXXXX"}
    human_name = key_data['human_name']
    key_type = key_data['key_type_human_name']
    key_val = key_data['redeemed_key_val']

    app = ShowKey(human_name, key_type, key_val)
    app.main_loop()


if __name__ == "__main__":
    main()
