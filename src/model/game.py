import abc
from typing import Dict, List, Optional

from galaxy.api.types import Game, LicenseType, LicenseInfo

from consts import Platform, KEY_TYPE
from model.download import DownloadStruct, TroveDownload, SubproductDownload


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


class Key(HumbleGame):
    @property
    def downloads(self):
        """No downloads for keys"""
        return {}

    @property
    def license(self) -> LicenseInfo:
        # second LicenseInfo argument - owner - can I pass there Steam/Origin user id?
        return LicenseInfo(LicenseType.OtherUserLicense, None)

    @property
    def human_name(self):
        return self._data['human_name']
    
    @property
    def key_type(self) -> KEY_TYPE:
        key_type = self._data['key_type']
        for typ in KEY_TYPE:
            if typ.value == key_type:
                return key_type
        raise TypeError(f'No such key type: {key_type}')
    
    @property
    def key_val(self) -> Optional[str]:
        """If returned value is None - the key was not revealed yet"""
        return self._data.get('redeemed_key_val')
