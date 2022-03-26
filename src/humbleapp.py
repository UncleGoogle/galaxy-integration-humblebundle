import json
import enum
import os
import pathlib
import typing as t
from dataclasses import dataclass
import webbrowser

from consts import WIN

if WIN:
    import winreg


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
class Settings:
    download_location: pathlib.Path


@dataclass
class HumbleAppConfig:
    settings: Settings
    game_collection: t.Dict[GameMachineName, VaultGame]


class FileWatcher:
    def __init__(self, path: pathlib.PurePath) -> None:
        self._path = path
        self._prev_mtime: float = 0.0
    
    @property
    def path(self) -> pathlib.PurePath:
        return self._path
    
    def has_changed(self) -> bool:
        last_mtime = os.stat(self._path).st_mtime
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
        
    games = {}
    for g_raw in content['game-collection-4']:
        g = parse_game(g_raw)
        games[g.machine_name] = g

    return HumbleAppConfig(
        settings=Settings(
            pathlib.Path(content['settings']['downloadLocation']),
        ),
        game_collection=games,
    )

    
def is_uri_handler_installed(protocol: str):
    """Source: https://github.com/FriendsOfGalaxy/galaxy-integration-origin/blob/master/src/uri_scheme_handler.py"""

    def _get_path_from_cmd_template(cmd_template: str) -> str:
        return cmd_template.replace("\"", "").partition("%")[0].strip()

    try:
        with winreg.OpenKey(
            winreg.HKEY_CLASSES_ROOT, r"{}\shell\open\command".format(protocol)
        ) as key:
            executable_template = winreg.QueryValue(key, None)
            path = _get_path_from_cmd_template(executable_template)
            return os.path.exists(path)
    except OSError:
        return False
    

class HumbleAppClient:
    PROTOCOL = "humble"

    @classmethod
    def _open(cls, cmd: str, arg: str):
        webbrowser.open(f"{cls.PROTOCOL}://{cmd}/{arg}")

    def is_installed(self):
        return self.is_uri_handler_installed(self.PROTOCOL)

    def launch_game(self, game_id: GameMachineName):
        self._open("launch", game_id)
    
    def install_game(self, game_id: GameMachineName):
        self._open("install", game_id)

