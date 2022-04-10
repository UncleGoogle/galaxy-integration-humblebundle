import json
import sys
import enum
import os
import pathlib
import logging
import typing as t
import webbrowser
from dataclasses import dataclass

IS_WINDOWS = sys.platform == 'win32'

if IS_WINDOWS:
    import winreg


logger = logging.getLogger(__name__)


Json = t.Dict[str, t.Any]
GameMachineName = str
Timestamp = int


class GameStatus(enum.Enum):
    AVAILABLE = "available"
    DOWNLOADED = "downloaded"
    INSTALLED = "installed"


class TroveCategory(enum.Enum):
    PREMIUM = "premium"
    GENERAL = "general"


@dataclass
class VaultGame:
    machine_name: GameMachineName
    game_name: str
    date_added: Timestamp
    date_ended: t.Optional[Timestamp]
    is_available: bool
    last_played: Timestamp
    file_size: int
    status: GameStatus
    trove_category: TroveCategory
    executable_path: t.Optional[str]
    file_path: t.Optional[str]
    
    @property
    def full_executable_path(self) -> t.Optional[pathlib.Path]:
        if self.file_path and self.executable_path:
            return pathlib.Path(self.file_path) / self.executable_path
    

@dataclass
class UserInfo:
    is_paused: bool
    owns_active_content: bool
    can_resubscribe: bool
    user_id: int
    has_ever_subscribed: bool
    has_perks: bool
    user_key: str
    has_beta_access: bool
    will_receive_future_months: bool


@dataclass
class  Settings:
    download_location: pathlib.Path


@dataclass
class HumbleAppConfig:
    settings: Settings
    game_collection: t.List[VaultGame]


class FileWatcher:
    def __init__(self, path: pathlib.PurePath) -> None:
        self._path = path
        self._prev_mtime: float = 0.0
    
    @property
    def path(self) -> pathlib.PurePath:
        return self._path
    
    def has_changed(self) -> t.Optional[bool]:
        try:
            last_mtime = os.stat(self._path).st_mtime
        except OSError:
            self._prev_mtime = None
            return None
        changed = last_mtime != self._prev_mtime
        self._prev_mtime = last_mtime
        return changed


def parse_humble_app_config(path: pathlib.PurePath)  -> HumbleAppConfig:
    def parse_game(raw):
        return VaultGame(
            machine_name=raw["machineName"],
            game_name=raw["gameName"],
            status=GameStatus(raw["status"]),
            is_available=raw["isAvailable"],
            last_played=Timestamp(raw["lastPlayed"]),
            file_size=raw["fileSize"],
            date_added=raw["dateAdded"],
            date_ended=raw["dateEnded"],
            trove_category=TroveCategory(raw["troveCategory"]),
            file_path=raw.get("filePath"),
            executable_path=raw.get("executablePath"),
        )
    
    with open(path, encoding="utf-8") as f:
        content = json.load(f)
        
    games = [parse_game(g) for g in content['game-collection-4']]

    return HumbleAppConfig(
        settings=Settings(
            pathlib.Path(content['settings']['downloadLocation']),
        ),
        game_collection=games,
    )

    
def get_app_path_for_uri_handler(protocol: str) -> t.Optional[str]:
    """Source: https://github.com/FriendsOfGalaxy/galaxy-integration-origin/blob/master/src/uri_scheme_handler.py"""

    if not IS_WINDOWS:
        return None

    def _get_path_from_cmd_template(cmd_template: str) -> str:
        return cmd_template.replace("\"", "").partition("%")[0].strip()

    try:
        with winreg.OpenKey(
            winreg.HKEY_CLASSES_ROOT, r"{}\shell\open\command".format(protocol)
        ) as key:
            executable_template = winreg.QueryValue(key, None)
            return _get_path_from_cmd_template(executable_template)
    except OSError:
        return None
    

class HumbleAppClient:
    PROTOCOL = "humble"

    @classmethod
    def _open(cls, cmd: str, arg: str):
        cmd = f"{cls.PROTOCOL}://{cmd}/{arg}"
        logger.info(f"Opening {cmd}")
        webbrowser.open(cmd)

    def get_exe_path(self) -> t.Optional[str]:
        return get_app_path_for_uri_handler(self.PROTOCOL)

    def is_installed(self):
        path = self.get_exe_path()
        if path:
            if os.path.exists(path):
                return True
            else:
                logger.debug(f"{path} does not exists")
        return False

    def launch(self, game_id: GameMachineName):
        self._open("launch", game_id)
    
    def install(self, game_id: GameMachineName):
        self._open("download", game_id)

    def uninstall(self, game_id: GameMachineName):
        self._open("uninstall", game_id)

