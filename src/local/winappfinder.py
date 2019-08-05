import logging
import asyncio
import pathlib
from typing import List, Optional

from consts import HP
from humblegame import HumbleGame
from local.pathfinder import PathFinder
from local.localgame import LocalHumbleGame
from local._reg_watcher import WindowsRegistryClient, UninstallKey


class WindowsAppFinder:
    def __init__(self):
        self._reg = WindowsRegistryClient()
        self._pathfinder = PathFinder(HP.WINDOWS)

    @staticmethod
    def _matches(human_name: str, uk: UninstallKey) -> bool:
        def escape(x):
            return x.replace(':', '').lower()
        def escaped_matches(a, b):
            return escape(a) == escape(b)
        def norm(x):
            return x.replace(" III", " 3").replace(" II", " 2")

        if human_name == uk.display_name \
            or escaped_matches(human_name, uk.display_name) \
            or uk.key_name.lower().startswith(human_name.lower()):
            return True
        if uk.install_location is not None:
            path = pathlib.PurePath(uk.install_location).name
            if escaped_matches(human_name, path):
                return True
        upath = uk.uninstall_string_path
        if upath and escape(human_name) in [escape(u) for u in upath.parts[1:]]:
            return True
        # quickfix for Torchlight II ect., until better solution will be provided
        return escaped_matches(norm(human_name), norm(uk.display_name))

    def _find_executable(self, human_name: str, uk: UninstallKey) -> Optional[pathlib.Path]:
        """ Returns most probable app executable of given uk or None if not found.
        """
        # sometimes display_icon link to main executable
        upath = uk.uninstall_string_path
        ipath = uk.display_icon
        if ipath and ipath.suffix == '.exe':
            if ipath != upath and 'unins' not in str(ipath):  # exclude uninstaller
                return ipath

        # get install_location if present; if not, check for uninstall or display_icon parents
        location = uk.install_location \
            or (upath.parent if upath else None) \
            or (ipath.parent if ipath else None)

        # find all executables and get best maching (exclude uninstall_path)
        if location and location.exists():
            executables = set(self._pathfinder.find_executables(location)) - {str(upath)}
            best_match = self._pathfinder.choose_main_executable(human_name, executables)
            if best_match is None:
                logging.warning(f'Main exe not found for {human_name}; \
                    loc: {uk.install_location}; up: {upath}; ip: {ipath}; execs: {executables}')
                return None
            return pathlib.Path(best_match)
        return None

    async def find_local_games(self, owned_games: List[HumbleGame]) -> List[LocalHumbleGame]:
        local_games = []
        while self._reg.uninstall_keys:
            uk = self._reg.uninstall_keys.pop()
            try:
                for og in owned_games:
                    if self._matches(og.human_name, uk):
                        exe = self._find_executable(og.human_name, uk)
                        if exe is not None:
                            local_games.append(LocalHumbleGame(og.machine_name, exe, uk.uninstall_string))
                            break
                        logging.warning(f"Uninstall key matched, but cannot find \
                            game exe for [{og.human_name}]; uk: {uk}")
            except Exception:
                self._reg.uninstall_keys.add(uk)
                raise
            await asyncio.sleep(0.001)  # makes this method non blocking
        return local_games


    def refresh(self):
        self._reg.refresh()
