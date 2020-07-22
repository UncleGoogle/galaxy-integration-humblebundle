import enum
import platform
import sys


class PlatformNotSupported(Exception):
    pass


class SOURCE(enum.Enum):
    DRM_FREE = 'drm-free'
    KEYS = 'keys'


class BITNESS(enum.Enum):
    B64 = 64
    B32 = 32


TROVE_SUBSCRIPTION_NAME = "Humble Trove"

NON_GAME_BUNDLE_TYPES = {'mobilebundle', 'softwarebundle', 'bookbundle', 'audiobookbundle', 'comicsbundle', 'rpgbookbundle', 'mangabundle'}

IS_WINDOWS = sys.platform == 'win32'
IS_MAC = sys.platform == 'darwin'

if platform.machine().endswith('64'):
    CURRENT_BITNESS = BITNESS.B64
else:
    CURRENT_BITNESS = BITNESS.B32

COMMA_SPLIT_BLACKLIST = [
    "About Love, Hate and the other ones",
    "Axe, Bow & Staff",
    "Bolt Riley, A Reggae Adventure - Chapter 1",
    "Borderlands 3: Guns, Love and Tentacles",
    "Codename: Panzers, Phase",
    "Cook, Serve, Delicious!",
    "Dude, Stop",
    "Duke Grabowski, Mighty Swashbuckler",
    "Football, Tactics & Glory",
    "Good Night, Knight",
    "Grand Theft Auto V, Criminal Enterprise Starter Pack",
    "Gremlins, Inc.",
    "Guns, Gore",
    "Hack, Slash & Backstab",
    "Hack, Slash, Loot",
    "Hamlet or the Last Game without MMORPG Features, Shaders and Product...",
    "Hot Dogs, Horseshoes & Hand Grenades",
    "Human, we have a problem",
    "I, Hope",
    "I, Zombie",
    "Invisible, Inc",
    "Just Cause™ 3: Air, Land & Sea Expansion Pass",
    "Mafia III - Faster, Baby!",
    "Magicka 2: Ice, Death, and Fury",
    "My Tower, My Home",
    "Orb Labs, Inc",
    "Papers, Please",
    "Sir, You Are Being Hunted",
    "Slow Down, Bull",
    "Sorry, James",
    "STAR WARS™ Battlefront (Classic, 2004)",
    "STAR WARS™ Battlefront™ II (Classic, 2005)",
    "That Dragon, Cancer",
    "The Haunted Island, a Frog Detective Game",
    "Total War Saga: THRONES OF BRITANNIA - Blood, Sweat and Spears",
    "Upwards, Lonely Robot",
    "Warlock 2: The Exiled - The Good, the Bad, & the Muddy",
]
