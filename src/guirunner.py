import sys
from typing import Callable, Optional, Iterable


class GUIError(Exception):
    pass


async def open(gui: str, *args, sensitive_args: Optional[Iterable]=None):
    import asyncio
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f'Running GUI [{gui}] with args: {args}')

    all_args = []
    if sensitive_args is not None:
        all_args = [gui] + list(args) + list(sensitive_args)

    process = await asyncio.create_subprocess_exec(
        sys.executable,
        __file__,  # self call
        *all_args,
        stderr=asyncio.subprocess.PIPE
    )
    _, stderr_data = await process.communicate()
    if stderr_data:
        logger.error(f'Error on running [{gui}]: {stderr_data}')
        raise GUIError(stderr_data)


if __name__ == '__main__':
    import pathlib

    parent_dir = pathlib.Path(__file__).parent
    sys.path.insert(0, str(parent_dir))  # our code
    sys.path.insert(0, str(parent_dir / 'modules'))  # third party

    from gui import ShowKey

    
    option = sys.argv[1]
    if option == 'keys':
        human_name = sys.argv[2]
        key_type = sys.argv[3]
        key_val = sys.argv[4]
        if key_val == 'None':
            key_val = None
        ShowKey(human_name, key_type, key_val).main_loop()
