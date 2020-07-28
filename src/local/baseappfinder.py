import logging
import asyncio
import difflib
import time
import os
import pathlib
import abc
from typing import Dict, Set, Iterable, Union, List, AsyncGenerator, Tuple
from typing import cast

from consts import IS_WINDOWS
from local.pathfinder import PathFinder
from local.localgame import LocalHumbleGame


logger = logging.getLogger('local')


class BaseAppFinder(abc.ABC):
    def __init__(self, get_close_matches=None, find_best_exe=None):
        self._pathfinder = PathFinder(IS_WINDOWS)
        self.get_close_matches = get_close_matches or self._get_close_matches
        self.find_best_exe = find_best_exe or self._find_best_exe

    async def __call__(self, owned_title_id: Dict[str, str], paths: Set[pathlib.Path]) -> Dict[str, LocalHumbleGame]:
        """
        :param owned_title_id: human_name: machine_name dictionary
        """
        start = time.time()
        found_games = await self._scan_folders(paths, set(owned_title_id))
        local_games = {
            owned_title_id[title]: LocalHumbleGame(owned_title_id[title], exe)
            for title, exe in found_games.items()
        }
        logger.debug(f'Scanning folders took {time.time() - start}')
        return local_games

    async def _scan_folders(self, paths: Iterable[Union[str, os.PathLike]], app_names: Set[str]) -> Dict[str, pathlib.Path]:
        """
        :param paths: all master paths to be scan for app finding
        :param app_names:  app names to be matched with folder names
        :returns:      mapping of app names to found executables
        """
        not_yet_found: Set[str] = app_names.copy()
        result: Dict[str, pathlib.Path] = {}
        close_matches: Dict[str, pathlib.Path] = {}
        # exact matches
        for path in paths:
            async for app_name, exe in self.__scan(path, not_yet_found, similarity=1):
                result[app_name] = exe
        # close matches
        for path in paths:
            async for app_name, exe in self.__scan(path, not_yet_found, similarity=0.8):
                close_matches[app_name] = exe
        # overwrite close matches with exact results
        close_matches.update(result)
        return close_matches

    async def __scan(self, path: Union[str, os.PathLike], candidates: Set[str], similarity: float) -> AsyncGenerator[Tuple[str, pathlib.Path], None]:
        """One level depth search generator for application execs based on similarity with candidate names.
        :param path:        root dir of which subdirectories will be scanned
        :param candidates:  set of app names used for exact and close matching with directory names
        :param similarity:  cutoff level for difflib.get_close_matches; set 1 for exact matching only
        :yields:            2-el. tuple of app_name and executable
        """
        root, dirs, _ = next(os.walk(path))
        logger.debug(f'New scan - similarity: {similarity}, candidates: {list(candidates)}')
        for dir_name in dirs:
            await asyncio.sleep(0)
            matches = self.get_close_matches(dir_name, candidates, similarity)
            for app_name in matches:
                dir_path = pathlib.PurePath(root) / dir_name
                best_exe = self.find_best_exe(dir_path, app_name)
                if best_exe is None:
                    logger.warning('No executable found, moving to next best matched app')
                    continue
                candidates.remove(app_name)
                yield app_name, pathlib.Path(best_exe)
                break

    def _get_close_matches(self, dir_name: str, candidates: Set[str], similarity: float) -> List[str]:
        """Wrapper around difflib.get_close_matches"""
        matches_ = difflib.get_close_matches(dir_name, candidates, cutoff=similarity)
        matches = cast(List[str], matches_)  # as str is Sequence[str] - mypy/issues/5090
        if matches:
            logging.info(f'Found close ({similarity}) matches for {dir_name}: {matches}')
        return matches

    def _find_best_exe(self, dir_path: pathlib.PurePath, app_name: str):
        executables = self._pathfinder.find_executables(dir_path)
        if not executables:
            return None
        logging.debug(f'Found execs: {executables}')
        return self._pathfinder.choose_main_executable(app_name, executables)
