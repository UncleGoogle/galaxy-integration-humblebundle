import re
import platform
import pathlib
from dataclasses import dataclass
from typing import Optional, Set, Dict
import winreg


@dataclass(frozen=True)
class UninstallKey:
    key_name: str
    display_name: str
    uninstall_string: str
    quiet_uninstall_string: Optional[str] = None
    _install_location: Optional[str] = None
    _display_icon: Optional[str] = None

    @property
    def install_location(self) -> Optional[pathlib.Path]:
        if not self._install_location:
            return None
        path = self._install_location.replace('"', '')
        return pathlib.Path(path)

    @property
    def display_icon(self) -> Optional[pathlib.Path]:
        if not self._display_icon:
            return None
        path = self._display_icon.split(',', 1)[0].replace('"', '')
        return pathlib.Path(path)

    @property
    def uninstall_string_path(self) -> Optional[pathlib.Path]:
        uspath = self.uninstall_string
        if not uspath:
            return None
        if uspath.startswith("MsiExec.exe"):
            return None
        if '"' not in uspath:
            return pathlib.Path(uspath)
        m = re.match(r'"(.+?)"', uspath)
        if m:
            return pathlib.Path(m.group(1))
        return None


class WindowsRegistryClient:
    _UNINSTALL_LOCATION = "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall"
    _LOOKUP_REGISTRY_HIVES = [winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE]

    def __init__(self):
        self.__uninstall_keys: Set[UninstallKey] = set()

        if self._is_os_64bit():
            self._ARCH_KEYS = [winreg.KEY_WOW64_32KEY, winreg.KEY_WOW64_64KEY]
        else:
            self._ARCH_KEYS = [0]

        self.__cache: Dict[int, Set[str]] = {
            arch | hive : set()  # subkey names
            for arch in self._ARCH_KEYS
            for hive in self._LOOKUP_REGISTRY_HIVES
        }

    @property
    def uninstall_keys(self):
        return self.__uninstall_keys

    @staticmethod
    def _is_os_64bit():
        return platform.machine().endswith('64')

    def __get_value(self, subkey, prop, optional=False):
        try:
            return winreg.QueryValueEx(subkey, prop)[0]
        except FileNotFoundError:
            if optional:
                return None
            raise

    def __parse_uninstall_key(self, name, subkey):
        return UninstallKey(
            key_name = name,
            display_name = self.__get_value(subkey, 'DisplayName'),
            uninstall_string = self.__get_value(subkey, 'UninstallString'),
            quiet_uninstall_string = self.__get_value(subkey, 'QuietUninstallString', optional=True),
            _display_icon = self.__get_value(subkey, 'DisplayIcon', optional=True),
            _install_location = self.__get_value(subkey, 'InstallLocation', optional=True),
        )

    def _iterate_new_uninstall_keys(self):
        for arch_key in self._ARCH_KEYS:
            for hive in self._LOOKUP_REGISTRY_HIVES:
                with winreg.OpenKey(hive, self._UNINSTALL_LOCATION, 0, winreg.KEY_READ | arch_key) as key:
                    subkeys = winreg.QueryInfoKey(key)[0]
                    # skip check if no changes since last check
                    # Note: dummy check for number of installed programs - intended to be called frequently
                    name_cache = self.__cache.get(hive | arch_key)
                    if subkeys <= len(name_cache):
                        continue

                    for i in range(subkeys):
                        subkey_name = winreg.EnumKey(key, i)
                        if subkey_name in name_cache:
                            continue
                        name_cache.add(subkey_name)
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            yield (subkey_name, subkey)

    def refresh(self):
        for name, subkey in self._iterate_new_uninstall_keys():
            try:
                ukey = self.__parse_uninstall_key(name, subkey)
            except FileNotFoundError:
                continue
            else:
                self.__uninstall_keys.add(ukey)

