import enum
import sys
import typing


class PlatformNotSupported(Exception):
    pass


class HP(enum.Enum):
    """HumbleBundle platform code name shown in subproducts>download section"""
    WINDOWS = 'windows'
    MAC = 'mac'
    LINUX = 'linux'
    ANDROID = 'android'
    AUDIO = 'audio'
    EBOOK = 'ebook'

    def __eq__(self, other):
        if type(other) == str:
            return self.value == other
        return super().__eq__(other)

    def __hash__(self):
        return hash(self.value)

GAME_PLATFORMS = set([HP.WINDOWS, HP.MAC, HP.LINUX])
DLC_PLATFORMS = [HP.AUDIO, HP.EBOOK]  # TODO push those with base game

if sys.platform == 'win32':
    CURRENT_SYSTEM = HP.WINDOWS
elif sys.platform == 'darwin':
    CURRENT_SYSTEM = HP.MAC
else:
    raise PlatformNotSupported('GOG Galaxy 2.0 supports only Windows and macos for now')

# typing aliases
Platform = typing.Union[HP, str]
