import enum
import pathlib
import os
import typing as t

from galaxy.api.types import SubscriptionGame, LocalGame, LocalGameState
from humbleapp.humbleapp import FileWatcher, GameStatus, TroveCategory, VaultGame, GameMachineName, HumbleAppConfig, parse_humble_app_config
from humbleapp.humbleapp import HumbleAppClient as _HumbleAppClient


class HumbleAppGameCategory(enum.Enum):
    HUMBLE_GAMES_COLLECTION = "Humble Games Collection"
    HUMBLE_VAULT = "Humble Vault"


SUBSCRIPTION_NAME_TO_TROVE_CATEGORY = {
    HumbleAppGameCategory.HUMBLE_GAMES_COLLECTION: TroveCategory.PREMIUM,
    HumbleAppGameCategory.HUMBLE_VAULT: TroveCategory.GENERAL
}


def _vault_to_galaxy_subscription_game(vault_game: VaultGame) -> SubscriptionGame:
    return SubscriptionGame(
        game_title=vault_game.game_name,
        game_id=vault_game.machine_name,
        start_time=vault_game.date_added,
        end_time=vault_game.date_ended
    )


def _vault_to_galaxy_local_game(vault_game: VaultGame) -> LocalGame:
    local_game_state_map = {
        GameStatus.AVAILABLE: LocalGameState.None_,
        GameStatus.DOWNLOADED: LocalGameState.None_,
        GameStatus.INSTALLED: LocalGameState.Installed,
    }
    return LocalGame(
        vault_game.machine_name,
        local_game_state_map[vault_game.status]
    )


class HumbleAppClient:
    CONFIG_PATH = pathlib.PurePath(os.path.expandvars(r"%appdata%")) / "Humble App" / "config.json"

    def __init__(self) -> None:
        self._client = _HumbleAppClient()
        self._config = FileWatcher(self.CONFIG_PATH)
        self._games: t.Dict[GameMachineName, VaultGame] = {} 
    
    def __contains__(self, game_id: str) -> bool:
        return game_id in self._games

    def get_subscription_games(self, subscription_name: HumbleAppGameCategory) -> t.List[SubscriptionGame]:
        category = SUBSCRIPTION_NAME_TO_TROVE_CATEGORY[subscription_name]
        return [
            _vault_to_galaxy_subscription_game(vg)
            for vg in self._games.values()
            if vg.trove_category is category
        ]

    def get_local_games(self) -> t.List[LocalGame]:
        return [
            _vault_to_galaxy_local_game(vg)
            for vg in self._games.values()
        ]

    def refresh_game_list(self) -> None:
        config = self._parse_config()
        if config is not None:
            self._games = {vg.machine_name: vg for vg in config.game_collection}
        
    def _parse_config(self) -> t.Optional[HumbleAppConfig]:
        if self._config.has_changed():
            return parse_humble_app_config(str(self.CONFIG_PATH))
        return None

    def is_installed(self) -> bool:
        return self._client.is_installed()
    
    def install(self, game_id: str) -> None:
        self._client.install(game_id)

    def uninstall(self, game_id: str) -> None:
        self._client.uninstall(game_id)

    def launch(self, game_id: str) -> None:
        self._client.launch(game_id)

    # TODO get local game size
    
    # TODO get os compatibility

    # TODO reconsider inheriting over HumbleGame instance to keep current convention