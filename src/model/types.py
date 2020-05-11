import enum


class HP(enum.Enum):
    """HumbleBundle platform code name shown in subproducts>download section"""
    WINDOWS = 'windows'
    MAC = 'mac'
    LINUX = 'linux'
    ANDROID = 'android'
    AUDIO = 'audio'
    EBOOK = 'ebook'
    ASMJS = 'asmjs'
    UNITYWASM = 'unitywasm'
    VIDEO = 'video'
    COMEDY = 'comedy'

    def __eq__(self, other):
        if type(other) == str:
            return self.value == other
        return super().__eq__(other)

    def __hash__(self):
        return hash(self.value)


GAME_PLATFORMS = set([HP.WINDOWS, HP.MAC, HP.LINUX])


class KEY_TYPE(enum.Enum):
    STEAM = 'steam'
    ORIGIN = 'origin'
    UPLAY = 'uplay'
    EPIC = 'epic'  # not sure about it
    BATTLENET = 'battlenet'  # not sure about it
    GOG = 'gog'  # not sure about it


class DeliveryMethod(enum.Enum):
    STEAM = 'steam'
    ORIGIN = 'origin'
    UPLAY = 'uplay'
    EPIC = 'epic'
    BATTLENET = 'battlenet'
    GOG = 'gog'
    DOWNLOAD = 'download'


class ExtrasType(enum.Enum):
    # TODO discover more
    DRM_FREE = 'DRM-free Game'