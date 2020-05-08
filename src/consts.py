import enum
import platform
import sys


class PlatformNotSupported(Exception):
    pass


class SUBSCRIPTIONS(enum.Enum):
    TROVE = 'Humble Trove'


class KEY_TYPE(enum.Enum):
    STEAM = 'steam'
    ORIGIN = 'origin'
    UPLAY = 'uplay'
    EPIC = 'epic'  # not sure about it
    BATTLENET = 'battlenet'  # not sure about it
    GOG = 'gog'  # not sure about it


class SOURCE(enum.Enum):
    DRM_FREE = 'drm-free'
    KEYS = 'keys'


class BITNESS(enum.Enum):
    B64 = 64
    B32 = 32


GAME_PLATFORMS = set([HP.WINDOWS, HP.MAC, HP.LINUX])
NON_GAME_BUNDLE_TYPES = {'mobilebundle', 'softwarebundle', 'bookbundle', 'audiobookbundle', 'comicsbundle', 'rpgbookbundle', 'mangabundle'}

IS_WINDOWS = sys.platform == 'win32'
IS_MAC = sys.platform == 'darwin'

if platform.machine().endswith('64'):
    CURRENT_BITNESS = BITNESS.B64
else:
    CURRENT_BITNESS = BITNESS.B32
