import abc
from typing import Dict, List, Optional

from galaxy.api.types import Game, LicenseType, LicenseInfo
from galaxy.api.consts import OSCompatibility

from consts import Platform, KEY_TYPE, HP
from model.download import TroveDownload, SubproductDownload


class InvalidHumbleGame(Exception):
    pass


class HumbleGame(abc.ABC):
    def __init__(self, data: dict):
        self._data = data
        self._minimal_validation()
    
    def _minimal_validation(self):
        try:
            self.in_galaxy_format()
        except KeyError as e:
            raise InvalidHumbleGame(repr(e))

    @abc.abstractmethod
    def downloads(self):
        pass

    @abc.abstractproperty
    def license(self) -> LicenseInfo:
        pass

    @property
    def human_name(self) -> str:
        return self._data['human_name']

    @property
    def machine_name(self) -> str:
        return self._data['machine_name']
    
    @property
    def os_compatibility(self) -> Optional[OSCompatibility]:
        compatibility = None
        if HP.WINDOWS in self.downloads:
            compatibility = OSCompatibility.Windows
        if HP.MAC in self.downloads:
            compatibility |= OSCompatibility.MacOS
        if HP.LINUX in self.downloads:
            compatibility |= OSCompatibility.Linux
        return compatibility

    def in_galaxy_format(self):
        dlcs = []  # not supported for now
        return Game(self.machine_name, self.human_name, dlcs, self.license)

    def __repr__(self):
        return str(self)

    def __str__(self):
        return f"<{self.__class__.__name__}> {self.human_name} : {self.machine_name}"
    
    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self._data == other._data


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


class Key(HumbleGame):
    @property
    def downloads(self):
        """No downloads for keys"""
        return {}

    @property
    def license(self) -> LicenseInfo:
        return LicenseInfo(LicenseType.OtherUserLicense, None)

    @property
    def key_type(self) -> KEY_TYPE:
        key_type = self._data['key_type']
        for typ in KEY_TYPE:
            if typ.value == key_type:
                return key_type
        raise TypeError(f'No such key type: {key_type}')

    @property
    def key_type_human_name(self) -> str:
        return self._data['key_type_human_name']

    @property
    def key_val(self) -> Optional[str]:
        """If returned value is None - the key was not revealed yet"""
        return self._data.get('redeemed_key_val')
