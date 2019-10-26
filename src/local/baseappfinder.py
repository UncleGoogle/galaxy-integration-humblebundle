import logging
import time
import pathlib
from typing import Dict, Set

from consts import CURRENT_SYSTEM
from local.pathfinder import PathFinder
from local.localgame import LocalHumbleGame


class BaseAppFinder:
    def __init__(self):
        self._pathfinder = PathFinder(CURRENT_SYSTEM)

    async def find_local_games(self, owned_title_id: Dict[str, str], paths: Set[pathlib.Path]) -> Dict[str, LocalHumbleGame]:
        """
        :param owned_title_id: human_name: machine_name dictionary
        """
        start = time.time()
        found_games = await self._pathfinder.scan_folders(paths, set(owned_title_id))
        local_games = {
            owned_title_id[title]: LocalHumbleGame(owned_title_id[title], exe)
            for title, exe in found_games.items()
        }
        logging.debug(f'=== Scan folders took {time.time() - start}')
        return local_games
