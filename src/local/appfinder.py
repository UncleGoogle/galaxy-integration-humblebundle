import os.path
import logging
import pathlib

from dataclasses import dataclass
from typing import Optional
from consts import CURRENT_SYSTEM, HP

from local.pathfinder import PathFinder

if CURRENT_SYSTEM == HP.WINDOWS:
    import winreg


@dataclass(frozen=True)
class UninstallKey:
    key_name: str
    display_name: str
    uninstall_cmd: str
    install_location: Optional[str]


class WindowsRegistryClient:
    UNINSTALL_LOCATION = "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall"
    LOOKUP_REGISTRY_HIVES = [winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE]

    def __init__(self):
        self.__uninstall_keys = []

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
                )
            except FileNotFoundError:
                print(f'key {name} do not have all required fields. Skip')
                continue
            else:
                self.__uninstall_keys.append(ukey)

    def _iterate_uninstall_keys(self):
        for hive in self.LOOKUP_REGISTRY_HIVES:
            with winreg.OpenKey(hive, self.UNINSTALL_LOCATION) as key:
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


class WindowsAppFinder:
    def __init__(self):
        self._reg = WindowsRegistryClient()
        self._pathfinder = PathFinder(HP.WINDOWS)

    @property
    def installed_apps(self):
        return self._reg.uninstall_keys

    def is_app_installed(self, human_name: str) -> bool:
        return bool(self.get_install_location(human_name))

    def get_install_location(self, human_name: str) -> str:
        for uk in self.installed_apps:
            if self.matches(human_name, uk):
                if os.path.exists(uk.install_location):
                    return uk.install_location

    def find_executable(self, human_name: str) -> Optional[pathlib.Path]:
        location = self.get_install_location(human_name)
        if location is None:
            return
        executables = self._pathfinder.find_executables(location)
        best_match = self._pathfinder.choose_best_executable(human_name, executables)
        if best_match is None:
            logging.warning(f'Main exe not found for {human_name}; reg location: {location}; executables: {executables}')
            return
        return pathlib.Path(best_match)

    @staticmethod
    def matches(human_name: str, uk: UninstallKey):
        def escaped_matches(a, b):
            def escape(x):
                return x.replace(':', '').lower()
            return escape(a) == escape(b)

        if human_name  == uk.display_name \
            or escaped_matches(human_name, uk.display_name) \
            or uk.key_name.startswith(human_name):
            return True
        elif uk.install_location is not None:
            path = pathlib.PurePath(uk.install_location).name
            return escaped_matches(human_name, path)
        return

    def refresh(self):
        self._reg.refresh()


if CURRENT_SYSTEM == HP.WINDOWS:
    AppFinder = WindowsAppFinder
elif CURRENT_SYSTEM == HP.MAC:
    AppFinder = None
else:
    raise RuntimeError(f'Unsupported system: {CURRENT_SYSTEM}')
