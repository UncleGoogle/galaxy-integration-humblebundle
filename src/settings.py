import pathlib
import logging
import toml
import os
from dataclasses import dataclass
from typing import Any, Dict, Callable, Mapping, Tuple, Optional, Set

from version import __version__
from consts import SOURCE


@dataclass
class LibrarySettings:
    sources: Tuple[SOURCE, ...] = (SOURCE.DRM_FREE, SOURCE.TROVE, SOURCE.KEYS)
    show_revealed_keys: bool = False

    def update(self, library: dict):
        sources = library.get('sources')
        show_keys = library.get('show_revealed_keys')

        if sources is not None:
            self.sources = tuple([SOURCE.match(s) for s in sources])
        if show_keys is not None:
            self.show_revealed_keys = show_keys
    
    def reset(self):
        self.sources = (SOURCE.DRM_FREE, SOURCE.TROVE, SOURCE.KEYS)
        self.show_revealed_keys = False
    
    @staticmethod
    def validate(library: dict):
        sources = library.get('sources')
        show_keys = library.get('show_revealed_keys')

        if show_keys and type(show_keys) != bool:
            raise TypeError(f'revealed_keys should be boolean (true or false), got {show_keys}')
        if sources and type(sources) != list:
            raise TypeError('Sources shoud be a list')
        if sources is not None:  # validate values
            [SOURCE.match(s) for s in sources]


class InstalledSettings:
    def __init__(self):
        self.search_dirs: Set[pathlib.Path] = set()

    def update(self, installed: dict):
        dirs = installed.get('search_dirs', [])
        self.search_dirs.clear()
        for i in dirs:
            expanded = os.path.expandvars(i)
            path = pathlib.Path(expanded).resolve()
            self.search_dirs.add(path)
        logging.info(f'Installed Settings: {self.search_dirs}')
    
    def reset(self):
        self.search_dirs.clear()
    
    @staticmethod
    def validate(installed: dict):
        dirs = installed.get('search_dirs', [])
        if type(dirs) != list:
            raise TypeError('search_paths shoud be list put in `[ ]`')
        for i in dirs:
            expanded = os.path.expandvars(i)
            path = pathlib.Path(expanded).resolve()
            if not path.exists():
                raise ValueError(f'Path {path} does not exists')


class Settings:
    LOCAL_CONFIG_FILE = pathlib.Path(__file__).parent / 'config.ini'

    def __init__(self, cache: Dict[str, str], save_cache_callback: Callable):
        self._curr_ver = __version__
        self._prev_ver = cache.get('version')
        self._cache = cache
        self._push_cache = save_cache_callback

        self._cached_config = toml.loads(cache.get('config', '')) 
        self._config: Dict[str, Any] = {}
        self._last_modification_time: Optional[float] = None

        self._library = LibrarySettings()
        self._installed = InstalledSettings()
        self.reload_local_config_if_changed(first_run=True)

    @property
    def library(self) -> LibrarySettings:
        return self._library
    
    @property
    def installed(self) -> InstalledSettings:
        return self._installed
    
    def _validate(self, config):
        self._library.validate(config['library'])
        self._installed.validate(config['installed'])

    def _reset_config(self):
        self._library.reset()
        self._installed.reset()
        self._config.clear()
    
    def _update_objects(self):
        self._library.update(self._config.get('library', {}))
        self._installed.update(self._config.get('installed', {}))
    
    def _load_config_file(self, config_path: pathlib.Path) -> Mapping[str, Any]:
        try:
            with open(config_path, 'r') as f:
                config = toml.load(f)
            self._validate(config)
            return config
        except Exception as e:
            logging.error('Parsing config file has failed. Details:\n' + repr(e))
            return {}

    def _update_user_config(self):
        """Simple migrations"""
        logging.info(f'Recreating user config file with new entries')
        data = toml.dumps(self._config)
        with open(self.LOCAL_CONFIG_FILE, 'r') as f:
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
            logging.exception(f'{path} not found. Clearing current config to use defaults')
            self._reset_config()
            return bool(self._last_modification_time)
        except Exception as e:
            logging.exception(f'Stating {path} has failed: {str(e)}')
            return False
        else:
            if stat.st_mtime != self._last_modification_time:
                self._last_modification_time = stat.st_mtime
                return True
            return False

    def reload_local_config_if_changed(self, first_run=False):
        if not self.has_config_changed():
            return

        local_config = self._load_config_file(self.LOCAL_CONFIG_FILE)
        logging.debug(f'local config: {local_config}')

        if first_run:
            if self._prev_ver is None or self._curr_ver <= self._prev_ver:
                self._config = {**self._cached_config, **local_config}
            else:  # prioritize cached config in case of plugin update
                self._config = {**local_config, **self._cached_config}
                logging.debug(f'updated config: {self._config}')
                if self._config.keys() - local_config.keys():
                    logging.debug(f'Config shape differs!')
                    self._update_user_config()
            if self._prev_ver != self._curr_ver:
                self._cache['version'] = self._curr_ver
        else:
            self._config.update(local_config)

        self._update_objects()
        self._cache['config'] = toml.dumps(self._config)
        self._push_cache()
