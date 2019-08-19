import pathlib
import logging
import shutil
import toml
import os
from typing import Any


class Settings:
    def __init__(self, config_dir: str):
        self.USER_CONFIG = pathlib.Path(config_dir) / 'config.toml'
        self.TEMPLATE_CONFIG = pathlib.Path(config_dir) / 'config_template.toml'

        self.library: Dict[str, Any] = {}  # merged config content
        self._config, self._user_config = {}, {}
        self._last_modification_time = None

        self._config = self.load_config_file(self.TEMPLATE_CONFIG)
        self._load_user_config()
        self._update_user_config()

    def _load_content(self):
        self.library = self._config.get('owned', {})

    def _load_user_config(self):
        if not self.USER_CONFIG.exists():
            logging.info(f'User config does not exists, creating using {self.USER_CONFIG.name}')
            try:
                shutil.copyfile(self.TEMPLATE_CONFIG, self.USER_CONFIG)
                self._user_config = {}
            except Exception as e:
                logging.error(e)
        else:
            self._user_config = self.load_config_file(self.USER_CONFIG)

        self._last_modification_time = os.stat(self.USER_CONFIG).st_mtime
        self._config.update(self._user_config)
        self._load_content()

    def _update_user_config(self):
        """Simple migrations"""
        if self._config.keys() - self._user_config.keys():
            logging.info(f'Recreating user config file with new entries')
            with open(self.USER_CONFIG, 'w') as f:
                toml.dump(self._config, f)

    @staticmethod
    def load_config_file(config_path: pathlib.Path):
        with open(config_path, 'r') as f:
            return toml.load(f)

    def reload_config_if_changed(self):
        path = self.USER_CONFIG
        try:
            stat = os.stat(path)
        except FileNotFoundError:
            raise
        except Exception as e:
            logging.exception(f'Stating {path} has failed: {str(e)}')
        else:
            if stat.st_mtime != self._last_modification_time:
                self._last_modification_time = stat.st_mtime
                self._load_user_config()
