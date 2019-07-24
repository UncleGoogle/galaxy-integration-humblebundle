import abc
import copy
from typing import Dict, Optional, List
from dataclasses import dataclass

from galaxy.api.types import Game, LicenseType, LicenseInfo

from consts import CURRENT_SYSTEM, PlatformNotSupported


class DownloadStruct(abc.ABC):
    """
    url: Dict[str, str]         # {'bittorent': str, 'web': str}
    file_size: str
    md5: str
    name: str
    uploaded_at: Optional[str]  # ex.: 2019-07-10T21:48:11.976780
    """
    def __init__(self, data: dict):
        self.__data = data
        self.url = data['url']

    @property
    def web(self):
        return self.url['web']

    @property
    def bittorrent(self):
        return self.url['bittorent']

    @abc.abstractmethod
    def human_size(self):
        pass


class TroveDownload(DownloadStruct):
    """ Additional fields:
    sha1: str
    timestamp: int          # ?
    machine_name: str
    size: str
    """
    def human_size(self):
        return self.__data['size']


class SubproductDownload(DownloadStruct):
    """ Additional fields:
    human_size: str
    """
    def human_size(self):
        return self.__data['human_size']



class HumbleGame(abc.ABC):
    def __init__(self, data: dict):
        self._data = data

    @abc.abstractmethod
    def downloads(self):
        pass

    @abc.abstractproperty
    def human_name(self):
        pass

    @property
    def machine_name(self):
        return self._data['machine_name']

    def in_galaxy_format(self):
        licence = LicenseInfo(LicenseType.SinglePurchase)
        dlcs = []  # not supported for now
        return Game(self.machine_name, self.human_name, dlcs, licence)

    def __repr__(self):
        return str(self)

    def __str__(self):
        return f"HumbleGame ({self.__class__.__name__}): ({self.human_name}, {self.downloads})"


class TroveGame(HumbleGame):
    @property
    def downloads(self) -> Dict[str, TroveDownload]:
        return {k: TroveDownload(v) for k, v in self._data['downloads']}

    @property
    def human_name(self):
        return self._data['human-name']


class Subproduct(HumbleGame):
    @property
    def downloads(self) -> Dict[str, List[SubproductDownload]]:
        return {dw['platform']: [SubproductDownload(x) for x in dw['download_struct']] for dw in self._data['downloads']}

    @property
    def human_name(self):
        return self._data['human_name']


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
