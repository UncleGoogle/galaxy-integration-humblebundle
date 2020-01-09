import pathlib
import webbrowser
from typing import Optional

from gui.baseapp import BaseApp
import toga


class ShowKey(BaseApp):
    SIZE = (40, 40)
    KEYS_URL = 'https://www.humblebundle.com/home/keys'

    def __init__(self, human_name: str, key_type: str, key_val: Optional[str]):
        self._key_type = key_type
        self._key_val = key_val
        revealed_info = ' (not revealed yet)' if self._key_val is None else ''
        self._info = f"{human_name}{revealed_info}:"
        super().__init__(f'{self._key_type} Key', self.SIZE, has_menu=False)

    def startup_method(self):
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
        return box

    def open_keys_url(self, _):
        print('opening', self.KEYS_URL)
        webbrowser.open(self.KEYS_URL)


def test():
    key_data = {"machine_name": "jumbo_machinarium_steam", "key_type": "steam", "key_type_human_name": "Steam", "human_name": "Machinarium", "redeemed_key_val": "DXLVR-XXXXX-XXXXX"}
    human_name = key_data['human_name']
    key_type = key_data['key_type_human_name']
    key_val = key_data['redeemed_key_val']

    app = ShowKey(human_name, key_type, key_val)
    app.main_loop()


if __name__ == "__main__":
    test()
