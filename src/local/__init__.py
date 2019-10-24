from consts import HP, CURRENT_SYSTEM


if CURRENT_SYSTEM == HP.WINDOWS:
    from local.winappfinder import WindowsAppFinder as AppFinder
elif CURRENT_SYSTEM == HP.MAC:
    from local.macappfinder import MacAppFinder as AppFinder  # type: ignore[misc]
else:
    raise RuntimeError(f'Unsupported system: {CURRENT_SYSTEM}')