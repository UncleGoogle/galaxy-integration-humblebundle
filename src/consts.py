import enum
import platform
import sys
import typing


class PlatformNotSupported(Exception):
    pass


class KEY_TYPE(enum.Enum):
    STEAM = 'steam'
    ORIGIN = 'origin'
    UPLAY = 'uplay'
    EPIC = 'epic'  # not sure about it
    BATTLENET = 'battlenet'  # not sure about it
    GOG = 'gog'  # not sure about it


class SOURCE(enum.Enum):
    DRM_FREE = 'drm-free'
    TROVE = 'trove'
    KEYS = 'keys'


class BITNESS(enum.Enum):
    B64 = 64
    B32 = 32


class HP(enum.Enum):
    """HumbleBundle platform code name shown in subproducts>download section"""
    WINDOWS = 'windows'
    MAC = 'mac'
    LINUX = 'linux'
    ANDROID = 'android'
    AUDIO = 'audio'
    EBOOK = 'ebook'
    ASMJS = 'asmjs'
    VIDEO = 'video'
    COMEDY = 'comedy'  # no idea

    def __eq__(self, other):
        if type(other) == str:
            return self.value == other
        return super().__eq__(other)

    def __hash__(self):
        return hash(self.value)


GAME_PLATFORMS = set([HP.WINDOWS, HP.MAC, HP.LINUX])
NON_GAME_BUNDLE_TYPES = {'mobilebundle', 'softwarebundle', 'bookbundle', 'audiobookbundle', 'comicsbundle', 'rpgbookbundle', 'mangabundle'}

if sys.platform == 'win32':
    CURRENT_SYSTEM = HP.WINDOWS
elif sys.platform == 'darwin':
    CURRENT_SYSTEM = HP.MAC
else:
    raise PlatformNotSupported('GOG Galaxy 2.0 supports only Windows and macos for now')

if platform.machine().endswith('64'):
    CURRENT_BITNESS = BITNESS.B64
else:
    CURRENT_BITNESS = BITNESS.B32
