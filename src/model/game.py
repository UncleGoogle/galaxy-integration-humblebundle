import abc
import logging
from typing import Dict, List, Optional, Any

from galaxy.api.types import Game, LicenseType, LicenseInfo
from galaxy.api.consts import OSCompatibility

from consts import KEY_TYPE, HP
from model.download import TroveDownload, SubproductDownload


HP_OS_MAP = {
    HP.WINDOWS: OSCompatibility.Windows,
    HP.MAC: OSCompatibility.MacOS,
    HP.LINUX: OSCompatibility.Linux
}
NO_OS = OSCompatibility.Windows ^ OSCompatibility.Windows


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

    @abc.abstractproperty
    def downloads(self) -> Dict[HP, Any]:
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
        compatibility = NO_OS
        for os_ in self.downloads.keys():
            compatibility |= HP_OS_MAP.get(os_, NO_OS)

        if compatibility == NO_OS:
            return None
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
    def downloads(self) -> Dict[HP, TroveDownload]:
        result = {}
        for k, v in self._data['downloads'].items():
            try:
                os_ = HP(k)
            except TypeError as e:  # log error and go forward
                logging.error(e, extra={'game': self})
            else:
                result[os_] = TroveDownload(v)
        return result

    @property
    def license(self) -> LicenseInfo:
        """There is currently not 'subscription' type license"""
        return LicenseInfo(LicenseType.OtherUserLicense)

    @property
    def human_name(self):
        return self._data['human-name']


class Subproduct(HumbleGame):
    @property
    def downloads(self) -> Dict[HP, List[SubproductDownload]]:
        result = {}
        for dw in self._data['downloads']:
            try:
                os_ = HP(dw['platform'])
            except TypeError as e:  # log error and go forward
                logging.error(e, extra={'game': self})
            else:
                result[os_] = [
                    SubproductDownload(x)
                    for x in dw['download_struct']
                ]
        return result

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
