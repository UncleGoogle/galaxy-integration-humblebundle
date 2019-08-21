import abc
from typing import Dict, List, Optional

from galaxy.api.types import Game, LicenseType, LicenseInfo

from consts import Platform


class DownloadStruct(abc.ABC):
    """
    url: Dict[str, str]         # {'bittorent': str, 'web': str}
    file_size: str
    md5: str
    name: str: Optional[str]  # asmjs downloads have no 'name'
    uploaded_at: Optional[str]  # ex.: 2019-07-10T21:48:11.976780
    """
    def __init__(self, data: dict):
        self._data = data
        self.url = data.get('url')

    @property
    def name(self) -> Optional[str]:
        return self._data.get('name')

    @property
    def web(self) -> Optional[str]:
        if self.url is None:
            return None
        return self.url['web']

    @property
    def bittorrent(self) -> Optional[str]:
        if self.url is None:
            return None
        return self.url.get('bittorrent')

    @abc.abstractmethod
    def human_size(self) -> str:
        pass


class TroveDownload(DownloadStruct):
    """ Additional fields:
    sha1: str
    timestamp: int          # ?
    machine_name: str
    size: str
    """
    @property
    def human_size(self):
        return self._data['size']

    @property
    def machine_name(self):
        return self._data['machine_name']


class SubproductDownload(DownloadStruct):
    """ Additional fields:
    human_size: str
    """
    @property
    def human_size(self):
        return self._data['human_size']


class HumbleGame(abc.ABC):
    def __init__(self, data: dict):
        self._data = data

    @abc.abstractmethod
    def downloads(self):
        pass

    @abc.abstractproperty
    def license(self) -> LicenseInfo:
        pass

    @abc.abstractproperty
    def human_name(self):
        pass

    @property
    def machine_name(self):
        return self._data['machine_name']

    def in_galaxy_format(self):
        dlcs = []  # not supported for now
        return Game(self.machine_name, self.human_name, dlcs, self.license)

    def __repr__(self):
        return str(self)

    def __str__(self):
        return f"<{self.__class__.__name__}> {self.human_name}, downloads: {self.downloads})"


class TroveGame(HumbleGame):
    @property
    def downloads(self) -> Dict[Platform, TroveDownload]:
        return {
            k: TroveDownload(v)
            for k, v in self._data['downloads'].items()
        }

    @property
    def license(self) -> LicenseInfo:
        """There is currently not 'subscription' type license"""
        return LicenseInfo(LicenseType.OtherUserLicense)

    @property
    def human_name(self):
        return self._data['human-name']


class Subproduct(HumbleGame):
    @property
    def downloads(self) -> Dict[Platform, List[SubproductDownload]]:
        return {
            dw['platform']: [
                SubproductDownload(x)
                for x in dw['download_struct']
            ]
            for dw in self._data['downloads']
        }

    @property
    def license(self) -> LicenseInfo:
        """There is currently not 'subscription' type license"""
        return LicenseInfo(LicenseType.SinglePurchase)

    @property
    def human_name(self):
        return self._data['human_name']
