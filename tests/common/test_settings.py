from unittest.mock import Mock, mock_open, patch, MagicMock
from pathlib import Path
from dataclasses import dataclass
import pytest
import toml

from settings import UpdateTracker, Settings, InstalledSettings

# -------- UpdateTracker ----------

@dataclass
class MockSection(UpdateTracker):
    key: bool

    def _update(self, key):
        if type(self.key) != type(key):
            raise TypeError
        self.key = key


def test_ut_has_changed_on_init():
    sec = MockSection(key=False)
    assert sec.has_changed() == True


def test_ut_has_changed_check_twice():
    sec = MockSection(key=False)
    assert sec.has_changed() == True
    assert sec.has_changed() == False


def test_ut_has_not_changed():
    sec = MockSection(key=False); sec.has_changed()
    sec.key = False
    assert sec.has_changed() == False


def test_ut_has_changed():
    sec = MockSection(key=False); sec.has_changed()
    sec.key = True
    assert sec.has_changed() == True


def test_ut_has_changed_quickly():
    sec = MockSection(key=False); sec.has_changed()
    sec.key = True
    sec.key = False
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
def settings():
    """
    :returns:     patched Settings instance just after init
    """
    with patch.object(Settings, 'dump_config'):
        # initialization without dumping config on local machine
        setts = Settings()
        setts.dump_config = Mock()  # reset mock
        yield setts


@pytest.fixture
def default_config():
    as_dict = Settings.DEFAULT_CONFIG
    as_string = toml.dumps(as_dict)
    return as_dict, as_string


def test_migrate_from_cache(settings):
    save_cache = Mock()
    user_cached_config = {
            "library": {
                "sources": ["drm-free", "trove", "keys"],
            }, "installed": {
                "search_dirs": [str(Path("C:/Games/Humble"))]
            }
        }
    cache = {
        "version": 1,
        "config": user_cached_config
    }
    settings.migration_from_cache(cache, save_cache)
    assert settings._config == user_cached_config
    settings.dump_config.assert_called_once()
    assert 'config' not in cache  # cleanup
    save_cache.assert_called_once()


# --------- Installed --------

def test_installed_defaults():
    installed = InstalledSettings()
    assert installed.has_changed() == True
    assert installed.search_dirs == set()
