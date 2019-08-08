import logging
import re
import asyncio
import pathlib
from typing import List, Optional

from consts import HP
from humblegame import HumbleGame
from local.pathfinder import PathFinder
from local.localgame import LocalHumbleGame
from local._reg_watcher import WinRegUninstallWatcher, UninstallKey


class WindowsAppFinder:
    def __init__(self):
        self._reg = WinRegUninstallWatcher(ignore_filter=self.is_other_store_game)
        self._pathfinder = PathFinder(HP.WINDOWS)

    @staticmethod
    def is_other_store_game(key_name) -> bool:
        """Exclude Steam and GOG games using uninstall key name.
        In the future probably more DRM-free stores should be supported
        """
        match = re.match(r'\d{10}_is1', key_name)  # GOG.com
        if match:
            return True
        return "Steam App" in key_name

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

        location = uk.install_location_path
        if location:
            if escaped_matches(human_name, location.name):
                return True
        else:
            location = uk.uninstall_string_path or uk.display_icon_path
            if location:
                if escaped_matches(human_name, location.parent.name):
                    return True

        # quickfix for Torchlight II ect., until better solution will be provided
        return escaped_matches(norm(human_name), norm(uk.display_name))

    def _find_executable(self, human_name: str, uk: UninstallKey) -> Optional[pathlib.Path]:
        """ Returns most probable app executable of given uk or None if not found.
        """
        # sometimes display_icon link to main executable
        upath = uk.uninstall_string_path
        ipath = uk.display_icon_path
        if ipath and ipath.suffix == '.exe':
            if ipath != upath and 'unins' not in str(ipath):  # exclude uninstaller
                return ipath

        # get install_location if present; if not, check for uninstall or display_icon parents
        location = uk.install_location_path \
            or (upath.parent if upath else None) \
            or (ipath.parent if ipath else None)

        # find all executables and get best machting (exclude uninstall_path)
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
                            game = LocalHumbleGame(og.machine_name, exe, uk.uninstall_string)
                            logging.info(f'New local game found: {game}')
                            local_games.append(game)
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
