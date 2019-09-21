from consts import CURRENT_SYSTEM, HP


if CURRENT_SYSTEM == HP.MAC:
    from .appfinder import AppFinder
if CURRENT_SYSTEM == HP.WINDOWS:
    from .winappfinder import WindowsAppFinder
    AppFinder = WindowsAppFinder
else:
    raise RuntimeError(f'Unsupported system: {CURRENT_SYSTEM}')
