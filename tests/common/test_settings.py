from unittest.mock import mock_open, patch
from pathlib import Path
from dataclasses import dataclass
import pytest

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
    
    def serialize(self):
        return self.key


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


# --------- Installed --------

def test_installed_defaults():
    installed = InstalledSettings()
    assert installed.has_changed() == True
    assert installed.search_dirs == set()


def test_installed_update_serialize(mocker):
    mocker.patch.object(Path, 'exists', return_value=True)
    if IS_WINDOWS:
        path = R"C:\Games\Humble Bundle"
    else:
        path = "/mnt/Games Drive"
    raw = {
        "search_dirs": [path]
    }
    installed = InstalledSettings()
    installed.update(raw)
    assert raw == installed.serialize()


@pytest.mark.skipif(not IS_WINDOWS, reason="test windows paths")
def test_installed_from_raw_file_allowed_paths(mocker):
    R"""Integration test starting from the raw file
    Note: single tick 'path\here' allows for raw interpretation in uses perser (toml)
    For 'path\\here' there will be error throwned (handled and ignored in the code)
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


def test_settings_default_config():
    """Default values comes directly from specific settings classes"""
    Settings()._config == {
        'library': LibrarySettings().serialize(),
        'installed': InstalledSettings().serialize()
    }
