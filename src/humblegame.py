from typing import Dict

from galaxy.api.types import Game, LicenseType, LicenseInfo

from consts import CURRENT_SYSTEM, PlatformNotSupported


class HumbleGame:
    def __init__(self, data):
        for k, v in data.items():
            setattr(self, k, v)

    def in_galaxy_format(self):
        licence = LicenseInfo(LicenseType.SinglePurchase)
        dlcs = []  # not supported for now
        return Game(self.machine_name, self.human_name, dlcs, licence)

    def __repr__(self):
        return str(self)

    def __str__(self):
        return f"HumbleGame({self.human_name}, {self.downloads})"


class HumbleDownloader:
    """Prepares downloads for specific conditionals"""
    def __init__(self, target_platrofm=CURRENT_SYSTEM, target_bitness=None, use_torrent=False):
        self.platform = target_platrofm
        self.bitness = target_bitness

    def find_best_url(self, downloads: dict) -> Dict[str, str]:
        system_downloads = list(filter(lambda x: x['platform'] == self.platform, downloads))

        if len(system_downloads) == 1:
            download_struct = system_downloads[0]['download_struct']
        elif len(system_downloads) == 0:
            platforms = [dw.platform for dw in downloads]
            raise PlatformNotSupported(f'{self.human_name} has only downloads for {platforms}')
        elif len(system_downloads) > 1:
            raise NotImplementedError('More system level conditionals required')

        download_items = list(filter(lambda x: x['name'] == 'Download', download_struct))

        if len(download_items) == 1:
            return download_items[0]['url']
        else:
            raise NotImplementedError(f'Found downloads: {len(download_items)}. All: {downloads}')
