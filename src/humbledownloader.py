from model.game import HumbleGame, TroveGame, Subproduct
from model.download import DownloadStruct, SubproductDownload, TroveDownload
from consts import CURRENT_SYSTEM, PlatformNotSupported, CURRENT_BITNESS, HP, BITNESS


class HumbleDownloadResolver:
    """Prepares downloads for specific conditionals"""
    def __init__(self, target_platform: HP=CURRENT_SYSTEM, target_bitness: BITNESS=CURRENT_BITNESS):
        self.platform = target_platform
        self.bitness = target_bitness

        if target_bitness == BITNESS.B64:
            self._expected_names = ['Download', '64-bit', '32-bit']
        else:
            self._expected_names = ['Download', '32-bit']

    def __call__(self, game: HumbleGame) -> DownloadStruct:
        if isinstance(game, TroveGame):
            return self._find_best_trove_download(game)
        elif isinstance(game, Subproduct):
            return self._find_best_subproduct_download(game)
        else:
            raise AssertionError('Unsupported game type')

    def _find_best_trove_download(self, game: TroveGame) -> TroveDownload:  # type: ignore[return]
        try:
            return game.downloads[self.platform]
        except KeyError:
            self.__platform_not_supported_handler(game)

    def _find_best_subproduct_download(self, game: Subproduct) -> SubproductDownload:
        try:
            system_downloads = game.downloads[self.platform]
        except KeyError:
            self.__platform_not_supported_handler(game)

        if len(system_downloads) == 1:
            return system_downloads[0]

        # choose download prioritizing lower indexes of self._expected_names
        for name in self._expected_names:
            for dw in system_downloads:
                if name == dw.name:
                    return dw
        raise NotImplementedError(f'Cannot decide which download to choose: {system_downloads}')

    def __platform_not_supported_handler(self, game):
        raise PlatformNotSupported(f'{game.human_name} has only downloads for {list(game.downloads.keys())}')
