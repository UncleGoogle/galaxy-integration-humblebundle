import pathlib
import logging
import toml
import os
from typing import Any, Dict, Callable, Mapping, List

from version import __version__
from consts import SOURCE


class Settings:
    LOCAL_CONFIG_FILE = pathlib.Path(__file__).parent / 'config.ini'
    DEFAULT_CONFIG = {
        'library': ['drm-free', 'trove', 'keys'],
        'show_revealed_keys': False
    }

    def __init__(self, cached_version: str, cached_config: str, save_cache_callback: Callable):
        self._curr_ver = __version__
        self._prev_ver = cached_version
        self._save_cache = save_cache_callback

        self._config: Dict[str, Any] = {}
        self._last_modification_time = None

        self._cached_config = toml.loads(cached_config)

        self.reload_local_config_if_changed(first_run=True)

    @property
    def sources(self) -> List[SOURCE]:
        config_sources = self._config.get('library', self.DEFAULT_CONFIG['library'])
        return [SOURCE.match(s) for s in config_sources]

    @property
    def show_revealed_keys(self):
        return self._config.get('show_revealed_keys', self.DEFAULT_CONFIG['show_revealed_keys'])

    @staticmethod
    def _load_config_file(config_path: pathlib.Path) -> Mapping[str, Any]:
        try:
            with open(config_path, 'r') as f:
                return toml.load(f)
        except Exception as e:
            logging.error('Parsing config file has failed. Default values will be used. Details:' + repr(e))
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

    def reload_local_config_if_changed(self, first_run=False):
        path = self.LOCAL_CONFIG_FILE
        try:
            stat = os.stat(path)
        except FileNotFoundError:
            logging.exception(f'{path} not found. Clearing current config to use defaults')
            self._config.clear()
        except Exception as e:
            logging.exception(f'Stating {path} has failed: {str(e)}')
            return
        else:
            if stat.st_mtime != self._last_modification_time:
                self._last_modification_time = stat.st_mtime
                local_config = self._load_config_file(self.LOCAL_CONFIG_FILE)

                if first_run:
                    if self._prev_ver is None or self._curr_ver <= self._prev_ver:
                        self._config = {**self._cached_config, **local_config}
                    else:  # prioritize cached config in case of plugin update
                        self._config = {**local_config, **self._cached_config}
                        self._save_cache('version', self._curr_ver)
                        if self._config.keys() - local_config.keys():
                            self._update_user_config()
                else:
                    self._config.update(local_config)

                self._save_cache('config', toml.dumps(self._config))
