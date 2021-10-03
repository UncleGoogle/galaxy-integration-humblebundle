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
    OTHER = 'other'
    _UNRECOGNIZED = 'unrecognized'

    @classmethod
    def _missing_(cls, value):
        return HP._UNRECOGNIZED

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


class Tier(enum.Enum):
    LITE = 'lite'
    BASIC = 'basic'
    PREMIUM = 'premium'
    CLASSIC = 'premiumv1'


class SubscriptionStatus(enum.Enum):
    NeverSubscribed = enum.auto()
    Expired = enum.auto()
    Active = enum.auto()
    Unknown = enum.auto()
    