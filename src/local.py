import os.path

from dataclasses import dataclass
from typing import Optional
from consts import CURRENT_SYSTEM, HP

if CURRENT_SYSTEM == HP.WINDOWS:
    import winreg


@dataclass
class UninstallKey:
    key_name: str
    display_name: str
    uninstall_cmd: str
    install_location: Optional[str]
    path: Optional[str]


class WindowsRegistryClient:
    UNINSTALL_LOCATION = "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall"
    LOOKUP_REGISTRIES = [winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE]

    def __init__(self):
        self.__uninstall_keys = {}  # Dict[str<display_name>, UninstallKey]
        self.refresh()

    def is_app_installed(self, name: str) -> bool:
        uk = self.get_uninstall_key(name)
        if uk:
            return os.path.exists(uk.install_location) or os.path.exists(uk.path)
    
    def get_uninstall_key(self, name: str) -> UninstallKey:
        """name is string to search for in registry uninstall keys.
        Keys names nad their display_name attribute are taken into account
        """
        for display_name, uk in self.__uninstall_keys.items():
            if name in [display_name, uk.key_name]:
                return uk

    @property
    def uninstall_keys(self):
        return self.__uninstall_keys

    def refresh(self):
        self.__uninstall_keys.clear()
        for name, subkey in self._iterate_uninstall_keys():
            try:
                ukey = UninstallKey(
                    key_name = name,
                    uninstall_cmd = self.__get_value(subkey, 'UninstallString'),
                    display_name = self.__get_value(subkey, 'DisplayName'),
                    install_location = self.__get_value(subkey, 'InstallLocation', optional=True),
                    path = self.__get_value(subkey, 'Path', optional=True)
                )
            except FileNotFoundError:
                continue
            else:
                self.__uninstall_keys[ukey.display_name] = ukey
    
    def _iterate_uninstall_keys(self):
        for regroot in self.LOOKUP_REGISTRIES:
            root = winreg.ConnectRegistry(None, regroot)

            with winreg.OpenKey(root, self.UNINSTALL_LOCATION) as key:
                subkeys = winreg.QueryInfoKey(key)[0]
                for i in range(subkeys):
                    subkey_name = winreg.EnumKey(key, i)
                    with winreg.OpenKey(key, subkey_name) as subkey:
                        try:
                            yield (subkey_name, subkey)
                        except FileNotFoundError:
                            continue

    def __get_value(self, subkey, prop, optional=False):
        try:
            return winreg.QueryValueEx(subkey, prop)[0]
        except FileNotFoundError:
            if optional:
                return None
            raise

