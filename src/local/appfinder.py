import pathlib
from typing import Dict, Any, List 

from consts import HP
from model.game import HumbleGame
from local.pathfinder import PathFinder
from local.localgame import LocalHumbleGame


class AppFinder:
    def __init__(self):
        self._pathfinder = PathFinder(HP.WINDOWS)

    async def find_local_games(self, owned_games: List[HumbleGame], config: Dict[str, Any]) -> List[LocalHumbleGame]:
        apps = {og.machine_name: og.human_name for og in owned_games}
        paths = config.get('master_paths', [])
        local_games = [
            LocalHumbleGame(id_, exe)
            for id_, exe in self._pathfinder.scan_folders(paths, apps).items()
        ]
        return local_games



