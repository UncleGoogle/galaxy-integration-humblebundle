import abc
import logging
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any

from galaxy.api.types import Game, LicenseType, LicenseInfo, SubscriptionGame

from model.types import KEY_TYPE, HP
from model.download import TroveDownload, SubproductDownload


class HumbleGame(abc.ABC):
    def __init__(self, data: dict):
        self._data = data

    @abc.abstractproperty
    def downloads(self) -> Dict[HP, Any]:
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
    def human_name(self):
        return self._data['human-name']

    def in_galaxy_format(self):
        return SubscriptionGame(game_title=self.human_name, game_id=self.machine_name)

    def serialize(self):
        return {
            'human-name': self._data['human-name'],
            'machine_name': self._data['machine_name'],
            'downloads': self._data['downloads']
        }


class Subproduct(HumbleGame):
    @property
    def downloads(self) -> Dict[HP, SubproductDownload]:
        result = {}
        for dw in self._data['downloads']:
            try:
                os_ = HP(dw['platform'])
            except TypeError as e:
                logging.warning(e, extra={'game': self._data})
            else:
                result[os_] = SubproductDownload(dw)
        return result

    @property
    def license(self) -> LicenseInfo:
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
        """Uses heuristics to add key identity if not already present.
        The heuristics may be wrong but it is not very harmfull."""
        key_type = super().key_type_human_name
        keywords = [" Key", key_type]
        for keyword in keywords:
            if keyword in self._game_name:
                return self._game_name
        return f'{self._game_name} ({key_type})'

    @property
    def machine_name(self):
        return self._game_id


@dataclass
class ChoiceGame(HumbleGame):
    id: str
    title: str
    slug: str
    is_extras: bool = False

    @property
    def machine_name(self):
        return self.id

    @property
    def human_name(self):
        return self.title

    @property
    def downloads(self):
        """No downloads for abstract choice games"""
        return {}

    @property
    def presentation_url(self):
        if self.is_extras:
            return f'https://www.humblebundle.com/subscription/{self.slug}'
        else:
            return f'https://www.humblebundle.com/subscription/{self.slug}/{self.id}'

    def in_galaxy_format(self):
        return SubscriptionGame(game_title=self.title, game_id=self.id)

    def serialize(self):
        return asdict(self)
