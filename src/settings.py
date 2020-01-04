import pathlib
import logging
import os
import subprocess
import abc
import configparser
from dataclasses import dataclass, field, astuple
from typing import Any, Dict, Callable, Mapping, Tuple, Optional, Set

import toml

from consts import SOURCE, HP, CURRENT_SYSTEM


logger = logging.getLogger(__name__)


class UpdateTracker(abc.ABC):
    """Base class to keep track of any change.
    Designed to be inherited by dataclasses."""

    def __serialize(self):
        return astuple(self)

    def __post_init__(self):
        # self.__first_call = True
        self.__prev = self.__serialize()
    
    def has_changed(self) -> bool:
        curr = self.__serialize()
        if self.__prev != curr:
            self.__prev = curr
            # return not self.__first_call
            return True
        return False

    def update(self, *args, **kwargs):
        """If any content validation error occurs: just logs and error and keep current state"""
        # self.__first_call = False
        try:
            self._update(*args, **kwargs)
        except Exception as e:
            logger.error(f"Parsing config error: {repr(e)}")
    
    @abc.abstractmethod
    def _update(self, *args, **kwargs):
        """Validates and updates section"""


@dataclass
class LibrarySettings(UpdateTracker):
    sources: Tuple[SOURCE, ...] = (SOURCE.DRM_FREE, SOURCE.TROVE, SOURCE.KEYS)
    show_revealed_keys: bool = False

    def _update(self, library):
        sources = library.get('sources')
        show_keys = library.get('show_revealed_keys')

        if sources and type(sources) != list:
            raise TypeError('sources should be a list')
        if show_keys and type(show_keys) != bool:
            raise TypeError(f'revealed_keys should be boolean (true or false), got {show_keys}')

        if sources is not None:
            self.sources = tuple([SOURCE(s) for s in sources])
        if show_keys is not None:
            self.show_revealed_keys = show_keys


@dataclass
class InstalledSettings(UpdateTracker):
    search_dirs: Set[pathlib.Path] = field(default_factory=set)

    def _update(self, installed):
    # def _update(self, config: configparser.ConfigParser())
        dirs = installed.get('search_dirs', [])

        if type(dirs) != list:
            raise TypeError('search_paths shoud be list put in `[ ]`')

        dirs_set = set()
        for i in dirs:
            expanded = os.path.expandvars(i)
            path = pathlib.Path(expanded).resolve()
            if not path.exists():
                raise ValueError(f'Path {path} does not exists')
            dirs_set.add(path)
        self.search_dirs = dirs_set


class Settings:
    if CURRENT_SYSTEM == HP.WINDOWS:
        LOCAL_CONFIG_FILE = pathlib.Path.home() / "AppData/Local/galaxy-hb/galaxy-hb.ini"
    else:
        LOCAL_CONFIG_FILE = pathlib.Path.home() / ".config/galaxy-hb.cfg"
    DEFAULT_CONFIG_FILE = pathlib.Path(__file__).parent / 'config.ini'
    DEFAULT_CONFIG = {
        "library": {
            "sources": ["drm-free", "keys"],
            "show_revealed_keys": True
        }, "installed": {
            "search_dirs": []
        }
    }

    def __init__(self):
        self._config: Dict[str, Any] = {}
        self._last_modification_time: Optional[float] = None

        self._library = LibrarySettings()
        self._installed = InstalledSettings()

        self._update_user_config()  # initial creation & migrations
        self.reload_config_if_changed()

    @property
    def library(self) -> LibrarySettings:
        return self._library
    
    @property
    def installed(self) -> InstalledSettings:
        return self._installed

    def open_config_file(self):
        logger.info('Opening config file')
        if CURRENT_SYSTEM == HP.WINDOWS:
            subprocess.Popen(['start', str(self.LOCAL_CONFIG_FILE.resolve())], shell=True)
        elif CURRENT_SYSTEM == HP.MAC:
            subprocess.Popen(['/usr/bin/open', '-t', '-n', str(self.LOCAL_CONFIG_FILE.resolve())])

    def _update_objects(self):
        self._library.update(self._config.get('library', {}))
        self._installed.update(self._config.get('installed', {}))
    
    def _load_config_file(self):
        try:
            with open(self.LOCAL_CONFIG_FILE, 'r') as f:
                self._config = toml.load(f)
        except FileNotFoundError:
            self._config = self.DEFAULT_CONFIG.copy()
        except Exception as e:
            logger.error('Parsing config file has failed. Details:\n' + repr(e))

    def _update_user_config(self):
        logger.info(f'Recreating user config in {self.LOCAL_CONFIG_FILE}')
        self.LOCAL_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = toml.dumps(self._config)
        with open(self.DEFAULT_CONFIG_FILE, 'r') as f:
            comment = ''
            for line in f.readlines():
                comment += line
                if line.strip() == '# ===':
                    break
        with open(self.LOCAL_CONFIG_FILE, 'w') as f:
            f.write(comment)
            f.write(data)
    
    def _has_config_changed(self) -> bool:
        path = self.LOCAL_CONFIG_FILE
        try:
            stat = path.stat()
        except FileNotFoundError:
            if self._last_modification_time is not None:
                logger.warning(f'Config at {path} were deleted')
                self._last_modification_time = None
        except Exception as e:
            logger.exception(f'Stating {path} has failed: {repr(e)}')
        else:
            if stat.st_mtime != self._last_modification_time:
                self._last_modification_time = stat.st_mtime
                return True
        return False

    def reload_config_if_changed(self) -> bool:
        if not self._has_config_changed():
            return False
        self._load_config_file()
        logger.debug(f'config: {self._config}')
        self._update_objects()
        return True


## configparser usage

# load default from code:
# p.read_dict(self.DEFAULT_CONFIG)

# load default from files:
# p.read(['config', 'default_config'])

# load:
# p = configparser.ConfigParser(allow_no_value=True)
# with open('config', 'r') as f:
#     p.read_file(f)
# for key, _ in p.items("installed_paths"):
#     path=pathlib.Path(key)
#     print(path)

# dump:
# p.set('installed_paths', str(pathlib.Path('path\four')))
# with open('config', 'w') as f:
#     p.write(f)

## logic:
# case 1: no config
# dump deafult config in home location 
# open welcome page

# case 2: config edited
# stat it on tick - reparse if needed
# -> parse_config

# case 3: config deleted
# log warning
# load default config

# for tests:
# parser.read_string("""
# ... [DEFAULT]
# ... hash = #
