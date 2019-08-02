from consts import CURRENT_SYSTEM, HP
from .localgame import LocalHumbleGame  # noqa
from .pathfinder import PathFinder


if CURRENT_SYSTEM == HP.WINDOWS:
    from ._winappfinder import WindowsAppFinder  # noqa
    AppFinder = WindowsAppFinder
elif CURRENT_SYSTEM == HP.MAC:
    AppFinder = None
else:
    raise RuntimeError(f'Unsupported system: {CURRENT_SYSTEM}')