import pathlib
import logging
import toml
import os
from dataclasses import dataclass
from typing import Any, Dict, Callable, Mapping, List, Tuple

from version import __version__
from consts import SOURCE


@dataclass
class OwnedSettings:
    sources: Tuple[SOURCE, ...] = (SOURCE.DRM_FREE, SOURCE.TROVE, SOURCE.KEYS)
    show_revealed_keys: bool = False

    def update(self, owned: dict):
        sources = owned.get('library')
        show_keys = owned.get('show_revealed_keys')

        if sources is not None:
            self.sources = tuple([SOURCE.match(s) for s in sources])
        if show_keys is not None:
            self.show_revealed_keys = show_keys
    
    def reset(self):
        self.sources = (SOURCE.DRM_FREE, SOURCE.TROVE, SOURCE.KEYS)
        self.show_revealed_keys = False
    
    @staticmethod
    def validate(owned: dict):
        sources = owned.get('library')
        show_keys = owned.get('show_revealed_keys')

        if show_keys and type(show_keys) != bool:
            raise TypeError(f'revealed_keys should be boolean (true or false), got {show_keys}')
        if sources and type(sources) != list:
            raise TypeError('Sources (library) shoud be a list')
        [SOURCE.match(s) for s in sources]


class Settings:
    LOCAL_CONFIG_FILE = pathlib.Path(__file__).parent / 'config.ini'

    def __init__(self, cached_version: str, cached_config: str, save_cache_callback: Callable):
        self._curr_ver = __version__
        self._prev_ver = cached_version
        self._save_cache = save_cache_callback

        self._cached_config = toml.loads(cached_config)
        self._config: Dict[str, Any] = {}
        self._last_modification_time = None

        self._owned = OwnedSettings()

        self.reload_local_config_if_changed(first_run=True)

    @property
    def owned(self) -> OwnedSettings:
        return self._owned
    
    def _save_config(self):
        self._owned.update(self._config.get('owned', {}))
        self._save_cache('config', toml.dumps(self._config))

    def _validate(self, config):
        self._owned.validate(config['owned'])

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
            for line in f.readline():
                comment += line
                if line == '# ===':
                    break
        with open(self.LOCAL_CONFIG_FILE, 'w') as f:
            f.write(comment)
            f.write(data)
    
    def has_config_changed(self) -> bool:
        path = self.LOCAL_CONFIG_FILE
        try:
            stat = os.stat(path)
        except FileNotFoundError:
            logging.exception(f'{path} not found. Clearing current config to use defaults')
            self._owned.reset()
            self._config.clear()
        except Exception as e:
            logging.exception(f'Stating {path} has failed: {str(e)}')
            return
        else:
            if stat.st_mtime != self._last_modification_time:
                self._last_modification_time = stat.st_mtime
                return True
            return False

    def reload_local_config_if_changed(self, first_run=False):
        if not self.has_config_changed():
            return

        local_config = self._load_config_file(self.LOCAL_CONFIG_FILE)
        logging.info(local_config)

        if first_run:
            if self._prev_ver is None or self._curr_ver <= self._prev_ver:
                self._config = {**self._cached_config, **local_config}
            else:  # prioritize cached config in case of plugin update
                self._config = {**local_config, **self._cached_config}
                if self._config.keys() - local_config.keys():
                    self._update_user_config()
                self._save_cache('version', self._curr_ver)
        else:
            self._config.update(local_config)

        self._save_config()
