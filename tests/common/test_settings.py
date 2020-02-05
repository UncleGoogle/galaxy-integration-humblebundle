from unittest.mock import Mock, mock_open, patch
from pathlib import Path
from dataclasses import dataclass
import pytest
import toml

from settings import UpdateTracker, Settings, InstalledSettings, LibrarySettings
from consts import IS_WINDOWS

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
    setts = Settings()
    setts.dump_config = Mock()
    return setts


def test_migrate_from_toml_cache(settings):
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
        "config": toml.dumps(user_cached_config)
    }
    settings.migration_from_cache(cache, save_cache)
    assert settings._config == user_cached_config
    settings.dump_config.assert_called_once()
    # settings are available just after migrations
    settings.library == LibrarySettings(user_cached_config['library'])
    # cleanup
    assert 'config' not in cache
    save_cache.assert_called_once()


# --------- Installed --------

def test_installed_defaults():
    installed = InstalledSettings()
    assert installed.has_changed() == True
    assert installed.search_dirs == set()


@pytest.mark.skipif(not IS_WINDOWS, reason="test windows paths")
def test_installed_from_raw_file_allowed_paths(mocker):
    """Integration test starting from the raw file
    Note: single tick 'path\here' allows for raw interpretation in uses perser (toml)
    For "path\\here" there will be error throwned (handled and ignored in the code)
    """
    config_content = r"""
    [library]
        sources = ["drm-free", "keys"]
    [installed]
        search_dirs = [
            'C:\Program Files(x86)\Humble',
            'D:\\Games',
            "E:\\Games",
        ]
    """
    mocker.patch.object(Path, 'exists', return_value=True)
    with patch('builtins.open', mock_open(read_data=config_content)):
        settings = Settings()
        assert settings.installed.search_dirs == {
            Path("C:\\Program Files(x86)\\Humble"),
            Path("D:\\Games"),
            Path("E:\\Games")
        }
