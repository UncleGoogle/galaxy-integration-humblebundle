from unittest.mock import Mock, mock_open
from pathlib import Path
from dataclasses import dataclass
import pytest
import toml

from settings import UpdateTracker, Settings

# -------- UpdateTracker ----------

@dataclass
class MockSection(UpdateTracker):
    key: bool

    def _update(self, key):
        if type(self.key) != type(key):
            raise TypeError
        self.key = key


def test_ut_has_not_changed():
    sec = MockSection(key=False)
    sec.key = False
    assert sec.has_changed() == False
    assert sec.has_changed() == False

def test_ut_has_changed():
    sec = MockSection(key=False)
    sec.key = True
    assert sec.has_changed() == True

def test_ut_has_changed_quickly():
    sec = MockSection(key=False)
    sec.key = True
    sec.key = False
    assert sec.has_changed() == False

def test_ut_has_changed_check_twice():
    sec = MockSection(key=False)
    sec.key = True
    assert sec.has_changed() == True
    assert sec.has_changed() == False

def test_ut_update_error(caplog):
    sec = MockSection(key=False)
    try:
        sec.update(key=1)
    except TypeError:
        pytest.fail('TypeError should not be raised')
    assert 'TypeError' in caplog.text
    assert sec.key == False, 'Key value should not be changed'


# ---------- Settings -----------


@pytest.fixture
def current_config():
    with open(Path(__file__).parents[2] / 'src' / 'config.ini', 'r') as f:
        raw = f.read()
    as_dict = toml.loads(raw)
    as_string = toml.dumps(as_dict)
    return raw, as_dict, as_string


# def test_migration_none_current(mocker, current_config):
#     """Acutally no migrations; curr version and curr config should be stored"""
#     mocker.patch('builtins.open', mock_open(read_data=current_config[0]))
#     save_cache = Mock()
#     cache = {}
#     settings = Settings()
#         cache=cache,
#         save_cache_callback=save_cache
#     )
#     assert cache['config'] == current_config[2]
#     assert cache['version'] == settings._curr_ver
#     save_cache.assert_called_once()


def test_load_config_installed_paths(mocker, current_config):
    home_dir = Path.home()
    config = current_config[1]
    config['installed']['search_dirs'] = [str(home_dir)]
    raw_conf = toml.dumps(config)

    mocker.patch('builtins.open', mock_open(read_data=raw_conf))
    settings = Settings()
    assert settings.installed.search_dirs == set([home_dir])
