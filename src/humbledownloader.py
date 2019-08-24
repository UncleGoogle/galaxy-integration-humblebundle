from model.game import HumbleGame, TroveGame, Subproduct
from model.download import DownloadStruct, SubproductDownload, TroveDownload
from consts import CURRENT_SYSTEM, PlatformNotSupported, CURRENT_BITNESS


class HumbleDownloadResolver:
    """Prepares downloads for specific conditionals"""
    def __init__(self, target_platform=CURRENT_SYSTEM, target_bitness=CURRENT_BITNESS):
        self.platform = target_platform
        self.bitness = target_bitness

        self._allowed_names = ['Download', '32-bit']
        if target_bitness == 64:
            self._allowed_names.append('64-bit')

    def __call__(self, game: HumbleGame) -> DownloadStruct:
        if isinstance(game, TroveGame):
            return self._find_best_trove_download(game)
        elif isinstance(game, Subproduct):
            return self._find_best_subproduct_download(game)
        else:
            raise AssertionError('Unsupported game type')

    def _find_best_trove_download(self, game: TroveGame) -> TroveDownload:  # type: ignore
        try:
            return game.downloads[self.platform]
        except KeyError:
            self.__platform_not_supporter_handler(game)

    def _find_best_subproduct_download(self, game: Subproduct) -> SubproductDownload:
        try:
            system_downloads = game.downloads[self.platform]
        except KeyError:
            self.__platform_not_supporter_handler(game)

        download_items = list(filter(lambda x: x.name in self._allowed_names, system_downloads))

        if len(download_items) == 1:
            return download_items[0]
        else:
            raise NotImplementedError(f'Found downloads: {len(download_items)}. All: {system_downloads}')

    def __platform_not_supporter_handler(self, game):
        raise PlatformNotSupported(f'{self.human_name} has only downloads for [{game.downloads.keys()}]')
