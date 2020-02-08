import abc
import logging
from typing import Dict, List, Optional, Any

from galaxy.api.types import Game, LicenseType, LicenseInfo

from consts import KEY_TYPE, HP
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

    @abc.abstractproperty
    def downloads(self) -> Dict[HP, Any]:
        pass

    @abc.abstractproperty
    def license(self) -> LicenseInfo:
        pass

    def os_compatibile(self, os: HP) -> bool:
        return os in self.downloads

    @property
    def human_name(self) -> str:
        return self._data['human_name']

    @property
    def machine_name(self) -> str:
        return self._data['machine_name']

    def in_galaxy_format(self):
        dlcs = []  # not supported for now
        truncated_name = self.human_name[:100]
        return Game(self.machine_name, truncated_name, dlcs, self.license)

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
            except TypeError as e:
                logging.warning(e, extra={'game': self._data})
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
            except TypeError as e:
                logging.warning(e, extra={'game': self._data})
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
        extra_safety_default = 'Key'
        return self._data.get('key_type_human_name', extra_safety_default)

    @property
    def key_val(self) -> Optional[str]:
        """If returned value is None - the key was not revealed yet"""
        return self._data.get('redeemed_key_val')
    
    @property
    def key_games(self) -> List['KeyGame']:
        """One key can represent multiple games listed in human_name.
        This property splits those games and returns list of KeyGame objects with incremental id.
        """
        names = self.human_name.split(', ')
        if len(names) == 1:
            return [KeyGame(self, self.machine_name, self.human_name)]
        else:
            return [
                KeyGame(self, f'{self.machine_name}_{i}', name)
                for i, name in enumerate(names)
            ]


class KeyGame(Key):
    """One key can represent multiple games listed in key.human_name"""
    def __init__(self, key: Key, game_id: str, game_name: str):
        self._game_name = game_name
        self._game_id = game_id
        super().__init__(key._data)
    
    @property
    def human_name(self):
        """Adds key identity if not already present"""
        key_type = super().key_type_human_name 
        keywords = [" Key", key_type]
        for keyword in keywords:
            if keyword in self._game_name or key_type in self._game_name:
                return self._game_name
        return f'{self._game_name} ({key_type})'

    @property
    def machine_name(self):
        return self._game_id
