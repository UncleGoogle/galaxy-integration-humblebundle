"""
This module serves for two things:
1) spawning GUI written in `gui` package (see __main__)
2) simple asyncio handler for 1) that cares about communication with GUI process

So handler 2) called from outside spawns separate python process that run 1).

Why? Because GUIs don't want to be spawn as not-main thread.
And also used `toga` toolkit cannot be pickled by `multiprocessing`
https://github.com/beeware/toga/issues/734

Toga is in developement stage and lacks many features especially for Windows. So why using it?
- it is OS native so is small in size (below 2MB) comparing to dozens/hundreds of MB for Qt/Wx
- Tkinter is not shipped by python preinstalled with Galaxy
- Galaxy allows to run webbrowser (chromium) only for user authentication. And to open local html file you need to setup local server
- Toga its nice, active project that needs support!
"""

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

    # Allow for imports from base level (sys.path is extended with the file parent).
    # Yes, I know it's not the best practise but `gui` is not reusable package, only code organiser
    parent_dir = pathlib.Path(__file__).parent
    sys.path.insert(0, str(parent_dir))  # our code
    sys.path.insert(0, str(parent_dir / 'modules'))  # third party

    from gui.keys import ShowKey
    from gui.options import Options

    # new root logger
    import logging
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # print also to stdout for better debugging
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    option = PAGE(sys.argv[1])
    if option == PAGE.KEYS:
        human_name, key_type, key_val = sys.argv[2:]  # pylint: disable=unbalanced-tuple-unpacking
        if key_val == 'None':
            key_val = None
        ShowKey(human_name, key_type, key_val).main_loop()
    elif option == PAGE.OPTIONS:
        Options().main_loop()
