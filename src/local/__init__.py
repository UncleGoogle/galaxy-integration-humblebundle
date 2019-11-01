from consts import HP, CURRENT_SYSTEM


if CURRENT_SYSTEM == HP.WINDOWS:
    from local.winappfinder import WindowsAppFinder as AppFinder  # noqa
elif CURRENT_SYSTEM == HP.MAC:
    from local.macappfinder import MacAppFinder as AppFinder  # type: ignore[misc] # noqa
else:
    raise RuntimeError(f'Unsupported system: {CURRENT_SYSTEM}')