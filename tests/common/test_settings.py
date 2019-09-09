from unittest.mock import Mock, mock_open
from pathlib import Path
import pytest
import toml

from settings import Settings
from version import __version__


@pytest.fixture
def current_config():
    with open(Path(__file__).parents[2] / 'src' / 'config.ini', 'r') as f:
        raw = f.read()
    as_dict = toml.loads(raw)
    as_string = toml.dumps(as_dict)
    return raw, as_dict, as_string


def test_migration_none_current(mocker, current_config):
    """Acutally no migrations; curr version and curr config should be stored"""
    mocker.patch('__main__.open', mock_open(read_data=current_config[0]))
    save_cache = Mock()
    cache = {}
    Settings(
        cache=cache,
        save_cache_callback=save_cache
    )
    assert cache['config'] == current_config[2]
    assert cache['version'] == __version__
    save_cache.assert_called_once()
