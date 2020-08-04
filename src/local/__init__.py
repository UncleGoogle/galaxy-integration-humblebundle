import logging

from consts import IS_MAC, IS_WINDOWS

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


if IS_WINDOWS:
    from local.winappfinder import WindowsAppFinder as AppFinder  # noqa
elif IS_MAC:
    from local.macappfinder import MacAppFinder as AppFinder  # type: ignore[misc] # noqa
else:
    raise RuntimeError(f'Unsupported system')