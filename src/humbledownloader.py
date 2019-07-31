from humblegame import DownloadStruct, HumbleGame, TroveGame, Subproduct, SubproductDownload, TroveDownload
from consts import CURRENT_SYSTEM, PlatformNotSupported


class HumbleDownloadResolver:
    """Prepares downloads for specific conditionals"""
    def __init__(self, target_platform=CURRENT_SYSTEM, target_bitness=None):
        self.platform = target_platform
        self.bitness = target_bitness

    def __call__(self, game: HumbleGame) -> DownloadStruct:
        if isinstance(game, TroveGame):
            return self._find_best_trove_download(game)
        elif isinstance(game, Subproduct):
            return self._find_best_subproduct_download(game)

    def _find_best_trove_download(self, game: TroveGame) -> TroveDownload:
        try:
            return game.downloads[self.platform]
        except KeyError:
            self.__platform_not_supporter_handler(game)

    def _find_best_subproduct_download(self, game: Subproduct) -> SubproductDownload:
        try:
            system_downloads = game.downloads[self.platform]
        except KeyError:
            self.__platform_not_supporter_handler(game)

        assert len(system_downloads) > 0

        if len(system_downloads) == 1:
            return system_downloads[0]
        else:
            download_items = list(filter(lambda x: x.name == 'Download', system_downloads))

        if len(download_items) == 1:
            return download_items[0]
        else:
            raise NotImplementedError(f'Found downloads: {len(download_items)}. All: {system_downloads}')

    def __platform_not_supporter_handler(self, game):
        raise PlatformNotSupported(f'{self.human_name} has only downloads for [{game.downloads.keys()}]')
