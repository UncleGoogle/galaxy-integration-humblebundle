"""
module origin:
https://github.com/FriendsOfGalaxy/galaxy-integration-battlenet/blob/master/src/pathfinder.py
"""
import os
import difflib
from pathlib import Path, PurePath
from typing import List, Optional

from consts import HP


class PathFinder(object):
    def __init__(self, system: HP):
        self.system = system

    def find_executables(self, folder: str) -> str:
        folder = Path(folder)
        if not folder.exists():
            raise FileNotFoundError(f'Pathfinder: {folder} does not exist')
        execs = []
        for root, dirs, files in os.walk(folder):
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
    def choose_main_executable(pattern: str, executables: List[os.PathLike]) -> Optional[str]:
        if len(executables) == 1:
            return executables[0]

        execs = {PurePath(k).stem: k for k in executables}
        no_cutoff = 0

        matches = difflib.get_close_matches(pattern, execs.keys(), cutoff=no_cutoff)
        if len(matches) > 0:
            # returns best match
            return execs.get(matches[0])
