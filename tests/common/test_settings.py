from unittest.mock import Mock, mock_open
from pathlib import Path
import pytest
import toml

from settings import Settings


@pytest.fixture
def current_config():
    with open(Path(__file__).parents[2] / 'src' / 'config.ini', 'r') as f:
        raw = f.read()
    as_dict = toml.loads(raw)
    as_string = toml.dumps(as_dict)
    return raw, as_dict, as_string


def test_migration_none_current(mocker, current_config):
    """Acutally no migrations; curr version and curr config should be stored"""
    mocker.patch('builtins.open', mock_open(read_data=current_config[0]))
    save_cache = Mock()
    cache = {}
    settings = Settings(
        cache=cache,
        save_cache_callback=save_cache
    )
    assert cache['config'] == current_config[2]
    assert cache['version'] == settings._curr_ver
    save_cache.assert_called_once()


def test_installed_paths_(mocker, current_config):
    home_dir = Path.home()
    config = current_config[1]
    config['installed']['search_dirs'] = [str(home_dir)]
    raw_conf = toml.dumps(config)

    mocker.patch('builtins.open', mock_open(read_data=raw_conf))
    settings = Settings(
        cache={},
        save_cache_callback=Mock()
    )
    assert settings.installed.search_dirs == set([home_dir])
