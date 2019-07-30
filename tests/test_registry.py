import pytest
from unittest.mock import patch
from contextlib import contextmanager

from local.appfinder import WindowsRegistryClient, UninstallKey, WindowsAppFinder


@pytest.fixture
def patch_wrc():
    @contextmanager
    def fn(subkeys):
        def mock_get_val(subkey, prop, optional=False):
            if optional:
                return subkey.get(prop)
            return subkey[prop]

        with patch.object(WindowsRegistryClient, "_iterate_uninstall_keys") as subkey_gen, \
             patch.object(WindowsRegistryClient, "_WindowsRegistryClient__get_value") as get_val:
            subkey_gen.return_value = iter(subkeys)
            get_val.side_effect = mock_get_val
            yield
    return fn


@pytest.fixture
def patch_os_path_exists():
    @contextmanager
    def fn(existing=True):
        if type(existing) == bool:
            with patch('os.path.exists', lambda _: existing):
                yield
        elif type(existing) == list:
            with patch('os.path.exists', lambda path: path in existing):
                yield
    return fn


@pytest.fixture
def annas_quest():
    mock_subkey = ("Anna's Quest_is1", {
        "DisplayName": "Anna's Quest",
        "InstallLocation": "D:\\Games\\Anna's Quest\\",
        "UninstallString": "\"D:\\Games\\Anna's Quest\\unins000.exe\""
    })
    uninstall_key = UninstallKey(
        key_name="Anna's Quest_is1",
        display_name="Anna's Quest",
        install_location="D:\\Games\\Anna's Quest\\",
        uninstall_cmd="\"D:\\Games\\Anna's Quest\\unins000.exe\""
    )
    return {"mock": mock_subkey, "uk": uninstall_key}


def test_basic_display_name(annas_quest, patch_wrc):
    human_name = "Anna's Quest"
    subkeys = [
        annas_quest['mock']
    ]
    expected = [
        annas_quest['uk']
    ]
    with patch_wrc(subkeys):
        finder = WindowsAppFinder()
        finder.refresh()
        assert finder._reg.uninstall_keys == expected
        assert finder.is_app_installed('Not existing app') == False
        with patch('os.path.exists', lambda _: True):
            assert finder.is_app_installed(human_name) == True
        with patch('os.path.exists', lambda _: False):
            assert finder.is_app_installed(human_name) == False


def test_match_with_folder_name(annas_quest, patch_wrc, patch_os_path_exists):
    human_name = "The Windosill"
    install_location = 'C:\\Games\\The Windosill\\'
    subkeys = [
        ("Windosill_is1", {
            "DisplayName": "Windosill version 1.61",
            "InstallLocation": install_location,
            "UninstallString": "\"C:\\Games\\The Windosill\\uninstall.exe\"",
        })
    ]
    with patch_wrc(subkeys), \
         patch('os.path.exists', lambda path: path == install_location):
        finder = WindowsAppFinder()
        finder.refresh()
        assert finder.is_app_installed(human_name) == True


def test_colon_in_name(annas_quest, patch_wrc, patch_os_path_exists):
    human_name = "Orks: final cutdown"
    install_location = "C:\\Games\\Orks Final Cutdown"
    subkeys = [
        ("Windosill_is1", {
            "DisplayName": "Orks Final Cutdown",
            "InstallLocation": install_location,
            "UninstallString": "",
        })
    ]
    with patch_wrc(subkeys), \
         patch('os.path.exists', lambda path: path == install_location):
        finder = WindowsAppFinder()
        finder.refresh()
        assert finder.is_app_installed(human_name) == True