from model.game import HumbleGame, TroveGame, Subproduct
from model.download import DownloadStructItem, SubproductDownload, TroveDownload
from consts import CURRENT_BITNESS, BITNESS


class HumbleDownloadResolver:
    """Prepares downloads for specific conditionals"""
    def __init__(self, target_bitness: BITNESS=CURRENT_BITNESS):
        if target_bitness == BITNESS.B64:
            self._expected_names = ['Download', '64-bit', '32-bit']
        else:
            self._expected_names = ['Download', '32-bit']

    def __call__(self, download: SubproductDownload) -> DownloadStructItem:
        download_struct = download.download_struct
        if len(download_struct) == 1:
            return download_struct[0]
        # choose download struct prioritizing lower indexes of self._expected_names
        for name in self._expected_names:
            for dw in download_struct:
                if name == dw.name:
                    return dw
        raise NotImplementedError(f'Cannot decide which download struct item to choose: {download_struct}')
