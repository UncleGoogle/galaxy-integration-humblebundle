import pathlib
import logging
import toml
import os
import subprocess
import configparser
import abc
from dataclasses import dataclass, field, astuple
from typing import Any, Dict, Callable, Mapping, Tuple, Optional, Set

from consts import SOURCE, HP, CURRENT_SYSTEM


class UpdateTracker(abc.ABC):
    """Base class to keep track of any change.
    Designed to be inherited by dataclasses."""
    # __first_call = True

    def __serialize(self):
        return astuple(self)

    def __post_init__(self):
        self.__prev = self.__serialize()
    
    def has_changed(self) -> bool:
        curr = self.__serialize()
        if self.__prev != curr:
            self.__prev = curr
            # if self.__first_call:
            #     self.__first_call = False
            #     return False
            return True
        return False

    def update(self, *args, **kwargs):
        """If any content validation error occurs: just logs and error and keep current state"""
        try:
            self._update(*args, **kwargs)
        except Exception as e:
            logging.error(f"Parsing config error: {repr(e)}")
    
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

    def _update(self, installed: dict):
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
        logging.info(f'Installed Settings: {self.search_dirs}')


class Settings:
    LOCAL_CONFIG_FILE = None # TODO: appdirs.user_config_dir(appname='galaxy_integration_humblebundle', appauthor=False)
    DEFAULT_CONFIG_FILE = pathlib.Path(__file__).parent / 'default_config.ini'
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
        self.reload_local_config_if_changed(first_run=True)

        # use configparser(?)
        # self._config = configparser.ConfigParser()
        # self._config.read_dict(self.DEFAULT_CONFIG)
        # >>> config = configparser.ConfigParser(allow_no_value=True)
        # for options liek "skip_sth". then check: if "skip_sth" in section

    @property
    def library(self) -> LibrarySettings:
        return self._library
    
    @property
    def installed(self) -> InstalledSettings:
        return self._installed
    
    def open_config_file(self):
        if CURRENT_SYSTEM == HP.WINDOWS:
            subprocess.run(['start', str(self.LOCAL_CONFIG_FILE.resolve())], shell=True)
        elif CURRENT_SYSTEM == HP.MAC:
            subprocess.run(['/usr/bin/open', str(self.LOCAL_CONFIG_FILE.resolve())])

    def _update_objects(self):
        self._library.update(self._config.get('library', {}))
        self._installed.update(self._config.get('installed', {}))
    
    def _load_config_file(self) -> Mapping[str, Any]:
        try:
            with open(self.LOCAL_CONFIG_FILE, 'r') as f:
                return toml.load(f)
        except Exception as e:
            logging.error('Parsing config file has failed. Details:\n' + repr(e))
            return {}

    def _update_user_config(self):
        logging.info(f'Recreating user config in {self.LOCAL_CONFIG_FILE}')
        data = toml.dumps(self._config)
        with open(self.DEFAULT_CONFIG, 'r') as f:
            comment = ''
            for line in f.readlines():
                comment += line
                if line.strip() == '# ===':
                    break
        with open(self.LOCAL_CONFIG_FILE, 'w') as f:
            f.write(comment)
            f.write(data)
    
    def has_config_changed(self) -> bool:
        path = self.LOCAL_CONFIG_FILE
        try:
            stat = path.stat()
        except FileNotFoundError:
            logging.exception(f'{path} not found.')
            # TODO what now? Redump default config? Do nothing? Reset to defaults?
        except Exception as e:
            logging.exception(f'Stating {path} has failed: {repr(e)}')
        else:
            if stat.st_mtime != self._last_modification_time:
                self._last_modification_time = stat.st_mtime
                return True
        return False

    def reload_local_config_if_changed(self, first_run=False) -> bool:
        if not self.has_config_changed():
            return False

        local_config = self._load_config_file(self.LOCAL_CONFIG_FILE)
        default_config = self._load_config_file(self.DEFAULT_CONFIG_FILE)
        logging.debug(f'local config: {local_config}')

        if first_run:
            # TODO config migrations here
            self._config = {**local_config, **default_config}
            if local_config != self._cached_config:
                self._update_user_config()
            self._cache['version'] = self._curr_ver
        else:
            self._config.update(local_config)

        self._update_objects()
        return True



# logic:
# case 1: no config
# dump deafult config in home location 
# open welcome page

# case 2: config edited
# stat it on tick - reparse if needed
# -> parse_config

# try:
#   parsed_raw = read()
# except ParseError as e:
#   log err
#   return

# try:
#   load_installed = load_installed(parsed_raw) 
# except LoadError:
#   log err

# try:
#   load_library = load_lib(parsed_raw)
# except LoadError:
#   log err
   
# what if installed-game_paths has changed: 
# parse it before matching heuristics, then redo all previous matching(?)

# for tests:
# parser.read_string("""
# ... [DEFAULT]
# ... hash = #

# def _getlist_converter(x: str):
#     return [i.strip() for i in x.split(',')]

# _CONVERTERS = {'list': _getlist_converter}
