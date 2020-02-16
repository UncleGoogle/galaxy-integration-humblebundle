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


async def _open(gui: PAGE, *args, sensitive_args: Optional[Iterable]=None):
    import asyncio
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f'Running [{gui}] with args: {args}')

    all_args = [gui.value] + list(args)
    if sensitive_args is not None:
        all_args += list(sensitive_args)

    process = await asyncio.create_subprocess_exec(
        sys.executable,
        __file__,  # this file for convenience
        *all_args,
        stderr=asyncio.subprocess.PIPE
    )
    _, stderr_data = await process.communicate()
    if stderr_data:
        if type(stderr_data) == bytes:
            try:
                stderr_data = stderr_data.decode('utf-8')
            except UnicodeDecodeError:
                pass
        raise GUIError(f'Error on running [{gui}]: {stderr_data}')


async def show_key(game: 'LocalGame'):
    await _open(
        PAGE.KEYS,
        game.human_name,
        game.key_type_human_name,
        sensitive_args=[game.key_val] if game.key_val is not None else []
    )


async def show_options(show_news: bool=False):
    args = [PAGE.OPTIONS]
    if show_news:
        args.append('--show_news')
    await _open(*args)


if __name__ == '__main__':
    import pathlib
    import argparse

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

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='page')

    options_parser = subparsers.add_parser(PAGE.OPTIONS.value)
    options_parser.add_argument('--show_news', action='store_true')

    keys_parser = subparsers.add_parser(PAGE.KEYS.value)
    keys_parser.add_argument('human_name')
    keys_parser.add_argument('key_type')
    keys_parser.add_argument('key_val', nargs='?', default=None)

    args = parser.parse_args()
    option = PAGE(args.page)

    if option == PAGE.OPTIONS:
        Options(args.show_news).main_loop()
    elif option == PAGE.KEYS:
        ShowKey(args.human_name, args.key_type, args.key_val).main_loop()
