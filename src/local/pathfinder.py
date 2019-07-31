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
        cutoff = 1
        cutoff_diff = 0.1
        best_match = None

        while cutoff > 0.1:
            res = difflib.get_close_matches(pattern, execs.keys(), cutoff=cutoff)
            if len(res) == 0:
                break
            else:
                best_match = res[0]
                if len(res) == 1:
                    break
            cutoff -= cutoff_diff

        return execs[best_match]
