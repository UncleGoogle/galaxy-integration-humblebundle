import re
import platform
import logging
import pathlib
from dataclasses import dataclass
from typing import Optional
import winreg

from consts import HP
from local.pathfinder import PathFinder
from local.localgame import LocalHumbleGame


@dataclass(frozen=True)
class UninstallKey:
    key_name: str
    display_name: str
    uninstall_string: str
    install_location: Optional[str] = None
    display_icon: Optional[str] = None
    quiet_uninstall_string: Optional[str] = None


class WindowsRegistryClient:
    _UNINSTALL_LOCATION = "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall"
    _LOOKUP_REGISTRY_HIVES = [winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE]

    def __init__(self):
        self.__uninstall_keys = []
        if self._is_os_64bit():
            self._ARCH_KEYS = [winreg.KEY_WOW64_32KEY, winreg.KEY_WOW64_64KEY]
        else:
            self._ARCH_KEYS = [0]

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
            display_icon = self.__get_value(subkey, 'DisplayIcon', optional=True),
            install_location = self.__get_value(subkey, 'InstallLocation', optional=True),
        )

    def _iterate_uninstall_keys(self):
        for view_key in self._ARCH_KEYS:
            for hive in self._LOOKUP_REGISTRY_HIVES:
                with winreg.OpenKey(hive, self._UNINSTALL_LOCATION, 0, winreg.KEY_READ | view_key) as key:
                    subkeys = winreg.QueryInfoKey(key)[0]
                    for i in range(subkeys):
                        subkey_name = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            yield (subkey_name, subkey)

    def refresh(self):
        self.__uninstall_keys.clear()
        for name, subkey in self._iterate_uninstall_keys():
            try:
                ukey = self.__parse_uninstall_key(name, subkey)
            except FileNotFoundError:
                # logging.debug(f'key {name} do not have all required fields. Skip')
                continue
            else:
                self.__uninstall_keys.append(ukey)


class WindowsAppFinder:
    def __init__(self):
        self._reg = WindowsRegistryClient()
        self._pathfinder = PathFinder(HP.WINDOWS)

    @staticmethod
    def __matches(human_name: str, uk: UninstallKey) -> bool:
        def escape(x):
            return x.replace(':', '').lower()
        def escaped_matches(a, b):
            return escape(a) == escape(b)
        def norm(x):
            # quickfix for Torchlight II ect., until better solution will be provided
            return x.replace(" III", " 3").replace(" II", " 2")

        if human_name == uk.display_name \
            or escaped_matches(human_name, uk.display_name) \
            or uk.key_name.startswith(human_name) \
            or escape(human_name) in uk.uninstall_string:
            return True
        if uk.install_location is not None:
            path = pathlib.PurePath(uk.install_location).name
            if escaped_matches(human_name, path):
                return True

        return escaped_matches(norm(human_name), norm(uk.display_name))

    @staticmethod
    def _get_path_from_install_location(sz_val: Optional[str]) -> Optional[pathlib.Path]:
        if not sz_val:
            return
        path = sz_val.replace('"', '')
        return pathlib.Path(path)

    @staticmethod
    def _get_path_from_display_icon(sz_val: Optional[str]) -> Optional[pathlib.Path]:
        if not sz_val:
            return
        path = sz_val.split(',', 1)[0].replace('"', '')
        return pathlib.Path(path)

    @staticmethod
    def _get_path_from_uninstall_string(sz_val: str) -> Optional[pathlib.Path]:
        if not sz_val:
            return
        if sz_val.startswith("MsiExec.exe"):  # no support for now
            return
        if '"' not in sz_val:
            return pathlib.Path(sz_val)
        m = re.match(r'"(.+?)"', sz_val)
        if m:
            return pathlib.Path(m.group(1))

    def _match_uninstall_key(self, human_name: str) -> UninstallKey:
        for uk in self._reg.uninstall_keys:
            if self.__matches(human_name, uk):
                return uk

    def find_executable(self, human_name: str, uk: UninstallKey) -> Optional[pathlib.Path]:
        """ Returns most probable app executable of given uk or None if not found.
        """
        # sometimes display_icon link to main executable
        upath = self._get_path_from_uninstall_string(uk.uninstall_string)
        ipath = self._get_path_from_display_icon(uk.display_icon)
        if ipath and ipath.suffix == '.exe':
            if ipath != upath and 'unins' not in str(ipath):  # exclude uninstaller!
                return ipath

        # get install_location if present; if not, check for uninstall or display_icon parents
        ildir = self._get_path_from_install_location(uk.install_location)
        udir = upath.parent if upath else None
        idir = ipath.parent if ipath else None
        location = ildir or udir or idir

        # find all executables and get best maching (exclude uninstall_path)
        if location and location.exists():
            executables = set(self._pathfinder.find_executables(location)) - {upath}
            best_match = self._pathfinder.choose_main_executable(human_name, executables)
            if best_match is None:
                logging.warning(f'Main exe not found for {human_name}; \
                    loc: {uk.install_location}; up: {upath}; ip: {ipath}; execs: {executables}')
                return
            return pathlib.Path(best_match)

    def find_local_game(self, machine_name: str, human_name: str) -> Optional[LocalHumbleGame]:
        uk = self._match_uninstall_key(human_name)
        if uk is not None:
            exe = self.find_executable(human_name, uk)
            if exe is not None:
                return LocalHumbleGame(machine_name, exe, uk.uninstall_string)
            logging.warning(f"Uninstall key found, but cannot find game location for [{human_name}]")

    def is_app_installed(self, human_name: str) -> bool:
        return bool(self.find_local_game(human_name))

    def refresh(self):
        self._reg.refresh()

