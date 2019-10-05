import os
import logging
import difflib
from pathlib import Path, PurePath
from typing import List, Optional, Union, Dict, Set

from consts import HP


class PathFinder(object):
    def __init__(self, system: HP):
        self.system = system

    def find_executables(self, path: Union[str, PurePath]) -> List[str]:
        folder = Path(path)

        if not folder.exists():
            raise FileNotFoundError(f'Pathfinder: {path} does not exist')
        execs = []
        for root, _, files in os.walk(folder):
            for path in files:
                whole_path = os.path.join(root, path)
                if self.is_exe(whole_path):
                    execs.append(whole_path)
        return execs

    def is_exe(self, path: str) -> bool:
        if self.system == HP.WINDOWS:
            return path.endswith('.exe')
        else:
            return os.access(path, os.X_OK)

    @staticmethod
    def choose_main_executable(pattern: str, executables: List[os.PathLike]) -> Optional[os.PathLike]:
        if len(executables) == 1:
            return executables[0]

        execs = {PurePath(k).stem.lower(): k for k in executables}
        no_cutoff = 0

        matches = difflib.get_close_matches(pattern.lower(), execs.keys(), cutoff=no_cutoff)
        if len(matches) > 0:
            # returns best match
            return execs.get(matches[0])  # type: ignore
        else:
            return None

    def scan_folders(self, paths: List[os.PathLike], app_names: Set[str]) -> Dict[str, Path]:
        """
        :param paths: all master paths to be scan for app finding
        :param app_names:  app names to be matched with folder names
        :returns      mapping of app names to found executables
        """
        def scan(path: os.PathLike, candidates: Set[str], similarity: float):
            root, dirs, _ = next(os.walk(path))
            for dir_name in dirs:
                logging.debug(f'candidates len should decrease: {len(candidates)}')
                matches = difflib.get_close_matches(dir_name.lower(), list(candidates), cutoff=similarity)
                if matches:
                    logging.info(f'found close ({similarity}) matches for {dir_name}: [{matches}]')
                for app_name in matches:
                    dir_path = PurePath(root) / dir_name
                    executables = self.find_executables(dir_path)
                    if not executables:
                        logging.warning(f'No executables found in matching folder {dir_path}')
                        continue
                    logging.debug(f'execs: {executables}')
                    best_exe = self.choose_main_executable(app_name, executables)
                    logging.info(f'best exe match: {best_exe}')
                    yield app_name, Path(best_exe)
                    break

        not_yet_found: Set[str] = app_names.copy()
        result: Dict[str, Path] = {}
        close_matches: Dict[str, Path] = {}

        # exact matches
        for path in paths:
            for app_name, exe in scan(path, not_yet_found, similarity=1):
                result[app_name] = exe
                not_yet_found.remove(app_name)  # small optimization by excluding already found apps

        # close matches
        for path in paths:
            for app_name, exe in scan(path, not_yet_found, similarity=0.8):
                close_matches[app_name] = exe

        # overwrite close matches with exact results
        close_matches.update(result)
        logging.debug(f'close_maches {close_matches}')

        return close_matches