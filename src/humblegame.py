import abc
import copy
from typing import Dict, Optional, List
from dataclasses import dataclass

from galaxy.api.types import Game, LicenseType, LicenseInfo

from consts import TP_PLATFORM


class DownloadStruct(abc.ABC):
    """
    url: Dict[str, str]         # {'bittorent': str, 'web': str}
    file_size: str
    md5: str
    name: str
    uploaded_at: Optional[str]  # ex.: 2019-07-10T21:48:11.976780
    """
    def __init__(self, data: dict):
        self._data = data
        self.url = data['url']

    @property
    def web(self):
        return self.url['web']

    @property
    def bittorrent(self):
        return self.url['bittorrent']

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
    def downloads(self) -> Dict[TP_PLATFORM, TroveDownload]:
        return {k: TroveDownload(v) for k, v in self._data['downloads'].items()}

    @property
    def human_name(self):
        return self._data['human-name']


class Subproduct(HumbleGame):
    @property
    def downloads(self) -> Dict[TP_PLATFORM, List[SubproductDownload]]:
        return {dw['platform']: [SubproductDownload(x) for x in dw['download_struct']] for dw in self._data['downloads']}

    @property
    def human_name(self):
        return self._data['human_name']

    @property
    def name(self):
        return self._data['name']

