import pathlib
import logging
import os
import subprocess
import abc
from dataclasses import dataclass, field, astuple
from typing import Any, Dict, Callable, Mapping, Tuple, Optional, Set

import toml

from consts import SOURCE, HP, CURRENT_SYSTEM


logger = logging.getLogger(__name__)


class UpdateTracker(abc.ABC):
    """Keeps track of any changes in a subclass.
    Default _serialize designed for dataclasses"""
    __prev = None

    def __serialize(self):
        return astuple(self)

    def has_changed(self) -> bool:
        curr = self.__serialize()
        if self.__prev != curr:
            self.__prev = curr
            return True
        return False

    def update(self, *args, **kwargs):
        """If any content validation error occurs: just logs an error and keep current state"""
        try:
            self._update(*args, **kwargs)
        except Exception as e:
            logger.error(f"Parsing config error: {repr(e)}")
    
    @abc.abstractmethod
    def _update(self, *args, **kwargs):
        """Validates and updates section"""


@dataclass
class LibrarySettings(UpdateTracker):
    sources: Tuple[SOURCE, ...] = tuple()
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
    DEFAULT_CONFIG_FILE = pathlib.Path(__file__).parent / 'config.ini'  # deprecated
    DEFAULT_CONFIG = {
        "library": {
            "sources": ["drm-free", "keys"],
            "show_revealed_keys": True
        }, "installed": {
            "search_dirs": []
        }
    }
    if CURRENT_SYSTEM == HP.WINDOWS:
        LOCAL_CONFIG_FILE = pathlib.Path.home() / "AppData/Local/galaxy-hb/galaxy-humble-config.ini"
    else:
        LOCAL_CONFIG_FILE = pathlib.Path.home() / ".config/galaxy-humble.cfg"

    def __init__(self):
        self._last_modification_time: Optional[float] = None

        self._config: Dict[str, Any] = self.DEFAULT_CONFIG.copy()
        self._library = LibrarySettings()
        self._installed = InstalledSettings()

        self._load_config_file()

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

    def reload_config_if_changed(self) -> bool:
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
                self._load_config_file()
                return True
        return False

    def _load_config_file(self):
        try:
            with open(self.LOCAL_CONFIG_FILE, 'r') as f:
                self._config = toml.load(f)
        except FileNotFoundError:
            self._config = self.DEFAULT_CONFIG.copy()
            logger.info(f'Config not found. Loaded default')
        except Exception as e:
            logger.error('Parsing config file has failed:\n' + repr(e))
            return
        else:
            logger.info(f'Loaded config: {self._config}')
        self._update_objects()

    def _update_objects(self):
        self._library.update(self._config.get('library', {}))
        self._installed.update(self._config.get('installed', {}))
    
    def dump_config(self):
        """Dumps content of self._config to config file, creating it if not exists."""
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

    def migration_from_cache(self, cache: Dict[str, Any], push_cache: Callable):
        """Copy cached config to new location."""
        cached_config = cache.get('config')
        if cached_config:
            logger.info(f'Migrating cached config: {cached_config}')
            self._config = toml.loads(cached_config)
            cache.pop('config', None)
            push_cache()
        self.dump_config()
