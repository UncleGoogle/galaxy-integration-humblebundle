import os
import logging
import difflib
from pathlib import Path, PurePath
from typing import List, Union, Sequence, Optional
from typing import cast


class PathFinder:
    def __init__(self, is_windows: bool):
        self.is_windows = is_windows

    def find_executables(self, path: Union[str, os.PathLike]) -> List[str]:
        folder = Path(path)

        if not folder.exists():
            raise FileNotFoundError(f'Pathfinder: {path} does not exist')
        execs: List[str] = []
        for root, _, files in os.walk(folder):
            for path in files:
                whole_path = os.path.join(root, path)
                if self.is_exe(whole_path):
                    execs.append(whole_path)
            break
        return execs

    def is_exe(self, path: str) -> bool:
        if self.is_windows:
            return path.endswith('.exe')
        else:
            return os.access(path, os.X_OK)

    @staticmethod
    def choose_main_executable(pattern: str, executables: Sequence[str]) -> Optional[str]:
        if len(executables) == 1:
            return executables[0]

        execs = {PurePath(k).stem.lower(): k for k in executables}
        no_cutoff = 0

        matches_ = difflib.get_close_matches(pattern.lower(), execs.keys(), cutoff=no_cutoff)
        matches = cast(List[str], matches_)  # as str is Sequence[str] - mypy/issues/5090
        try:
            best_match = matches[0]
        except IndexError:
            logging.error(f'Empty list returns from get_close_matches {pattern}, {executables}')
            return None
        else:
            return execs[best_match]
