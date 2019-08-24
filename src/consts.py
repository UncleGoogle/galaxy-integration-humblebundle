import enum
import platform
import sys
import typing


class PlatformNotSupported(Exception):
    pass


class KEY_TYPE(enum.Enum):
    STEAM = 'steam'
    ORIGIN = 'origin'


class SOURCE(enum.Enum):
    LIBRARY = 'drm-free'
    TROVE = 'trove'
    KEYS = 'keys'
    
    @classmethod
    def match(cls, val):
        for it in cls:
            if it.value == val:
                return it
        raise TypeError(f'No such enum value: {val}. Available: {[it.value for it in cls]}')


class HP(enum.Enum):
    """HumbleBundle platform code name shown in subproducts>download section"""
    WINDOWS = 'windows'
    MAC = 'mac'
    LINUX = 'linux'
    ANDROID = 'android'
    AUDIO = 'audio'
    EBOOK = 'ebook'
    ASMJS = 'asmjs'

    def __eq__(self, other):
        if type(other) == str:
            return self.value == other
        return super().__eq__(other)

    def __hash__(self):
        return hash(self.value)

GAME_PLATFORMS = set([HP.WINDOWS, HP.MAC, HP.LINUX])
DLC_PLATFORMS = set([HP.AUDIO, HP.EBOOK])  # TODO push those with base game

# TODO check for more types to filter out. audiobundle?
NON_GAME_BUNDLE_TYPES = {'mobilebundle', 'softwarebundle', 'bookbundle'}
FREE_GAME_BUNDLES_TYPES = {'freegame', 'free'}  # at least one free game machine_name ends with 'free'

if sys.platform == 'win32':
    CURRENT_SYSTEM = HP.WINDOWS
elif sys.platform == 'darwin':
    CURRENT_SYSTEM = HP.MAC
else:
    raise PlatformNotSupported('GOG Galaxy 2.0 supports only Windows and macos for now')

if platform.machine().endswith('64'):
    CURRENT_BITNESS = 64
else:
    CURRENT_BITNESS = 32

# typing aliases
Platform = typing.Union[HP, str]
