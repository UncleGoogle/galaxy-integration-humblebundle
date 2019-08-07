from consts import CURRENT_SYSTEM, HP


if CURRENT_SYSTEM == HP.WINDOWS:
    from .winappfinder import WindowsAppFinder  # noqa
    AppFinder = WindowsAppFinder()
elif CURRENT_SYSTEM == HP.MAC:
    AppFinder = None  # type: ignore
else:
    raise RuntimeError(f'Unsupported system: {CURRENT_SYSTEM}')
