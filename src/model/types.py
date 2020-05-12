import enum


class HP(enum.Enum):
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
    OCULUS = 'oculus-rift'
    VIVE = 'vive'

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
    EPIC = 'epic'
    BATTLENET = 'battlenet'
    GOG = 'gog'


class DeliveryMethod(enum.Enum):
    STEAM = 'steam'
    ORIGIN = 'origin'
    UPLAY = 'uplay'
    EPIC = 'epic'
    BATTLENET = 'battlenet'
    GOG = 'gog'
    DOWNLOAD = 'download'
