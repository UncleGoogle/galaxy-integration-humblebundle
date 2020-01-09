import sys
import enum
from typing import Optional, Iterable


class PAGE(enum.Enum):
    KEYS = 'keys'
    OPTIONS = 'options'


class GUIError(Exception):
    pass


async def open(gui: PAGE, *args, sensitive_args: Optional[Iterable]=None):
    import asyncio
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f'Running [{gui}] with args: {args}')

    all_args = [gui.value] + list(args)
    if sensitive_args is not None:
        all_args += list(sensitive_args)

    process = await asyncio.create_subprocess_exec(
        sys.executable,
        __file__,  # the same file for convenience
        *all_args,
        stderr=asyncio.subprocess.PIPE
    )
    _, stderr_data = await process.communicate()
    if stderr_data:
        raise GUIError(f'Error on running [{gui}]: {stderr_data}')


async def show_key(game: 'LocalGame'):
    await open(
        PAGE.KEYS,
        game.human_name,
        game.key_type_human_name,
        sensitive_args=[str(game.key_val)]
    )


if __name__ == '__main__':
    import pathlib

    parent_dir = pathlib.Path(__file__).parent
    sys.path.insert(0, str(parent_dir))  # our code
    sys.path.insert(0, str(parent_dir / 'modules'))  # third party

    from gui.keys import ShowKey
    from gui.options import Options


    option = PAGE(sys.argv[1])
    if option == PAGE.KEYS:
        human_name, key_type, key_val = sys.argv[2:]  # pylint: disable=unbalanced-tuple-unpacking
        if key_val == 'None':
            key_val = None
        ShowKey(human_name, key_type, key_val).main_loop()
    elif option == PAGE.OPTIONS:
        Options().main_loop()


