import pytest
import pathlib
from unittest.mock import patch
from contextlib import contextmanager

from local._winappfinder import WindowsRegistryClient, UninstallKey, WindowsAppFinder


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
def annas_quest():
    mock_subkey = ("Anna's Quest_is1", {
        "DisplayName": "Anna's Quest",
        "InstallLocation": "D:\\Games\\Anna's Quest\\",
        "UninstallString": "\"D:\\Games\\Anna's Quest\\unins000.exe\""
    })
    uninstall_key = UninstallKey(
        key_name="Anna's Quest_is1",
        display_name="Anna's Quest",
        uninstall_string="\"D:\\Games\\Anna's Quest\\unins000.exe\"",
        _install_location="D:\\Games\\Anna's Quest\\",
    )
    return {"mock": mock_subkey, "uk": uninstall_key}


@pytest.fixture
def uk_torchlight2():
    """In this real example, there is no installLocation and displayIcon links to launcher executable.
    """
    return UninstallKey(
        key_name = "{049FF5E4-EB02-4c42-8DB0-226E2F7A9E53}",
        display_name = "Torchlight 2",
        uninstall_string = R"C:\Users\Public\Games\Runic Games\Torchlight 2\uninstall.exe",
        _install_location = None,
        _display_icon = R"C:\Users\Public\Games\Runic Games\Torchlight 2\ModLauncher.exe",
    )


# ---------- UninstallKey -----------

def test_uk_display_icon_path():
    display_icons = ["\"C:\\abc\\s.ico\",0", "C:\\abc\\s.ico,1", "C:\\abc\\s.ico", "\"C:\\abc\\s.ico\""]
    for i in display_icons:
        uk = UninstallKey('', '', '', _display_icon=i)
        assert pathlib.Path("C:\\abc\\s.ico") == uk.display_icon


def test_uk_uninstall_string_path():
    expected = pathlib.Path(R"D:\Games\HoMM 3 Complete\unins000.exe")
    uninstall_strings = [
        R'D:\Games\HoMM 3 Complete\unins000.exe',
        R'"D:\Games\HoMM 3 Complete\unins000.exe"',
        R'"D:\Games\HoMM 3 Complete\unins000.exe" /SILENT',
        R'"D:\Games\HoMM 3 Complete\unins000.exe" uninstall extra_path "C:\ProgramData\HoMM\saves"'
        R'"D:\Games\HoMM 3 Complete\unins000.exe" --lang=esMX, --display-name="Heroes 3"'
    ]
    for i in uninstall_strings:
        uk = UninstallKey('', '', uninstall_string=i)
        assert expected == uk.uninstall_string_path


def test_uk_uninstall_string_path_empty():
    assert None == UninstallKey('', '', uninstall_string='').uninstall_string_path


def test_uk_uninstall_string_path_msi():
    """No support for msi uninstallers for now"""
    path = 'MsiExec.exe /I{20888FA1-8127-42E3-969F-9BF93245AC83}'
    uk = UninstallKey('', '', uninstall_string=path)
    assert None == uk.uninstall_string_path


# --------- WindowsAppFinder -----------

def test_match_basic_display_name(annas_quest, patch_wrc):
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
        assert annas_quest['uk'] == finder._match_uninstall_key(human_name)


def test_match_with_folder_name(patch_wrc):
    human_name = "The Windosill"
    install_location = 'C:\\Games\\The Windosill\\'
    subkeys = [
        ("Windosill_is1", {
            "DisplayName": "Windosill version 1.61",
            "InstallLocation": install_location,
            "UninstallString": "\"C:\\Games\\The Windosill\\uninstall.exe\"",
        })
    ]
    with patch_wrc(subkeys):
        finder = WindowsAppFinder()
        finder.refresh()
        assert install_location == finder._match_uninstall_key(human_name)._install_location


def test_match_colon_in_name(patch_wrc):
    human_name = "Orks: final cutdown"
    install_location = "C:\\Games\\Orks Final Cutdown"
    subkeys = [
        ("Windosill_is1", {
            "DisplayName": "Orks Final Cutdown",
            "InstallLocation": install_location,
            "UninstallString": "",
        })
    ]
    with patch_wrc(subkeys):
        finder = WindowsAppFinder()
        finder.refresh()
        assert install_location == finder._match_uninstall_key(human_name)._install_location


def test_no_match(annas_quest, patch_wrc):
    human_name = "Orks: final cutdown"
    subkeys = [
        ("orkgame_is1", {
            "DisplayName": "Ork game",
            "InstallLocation": "C:\\OrkGame\\",
            "UninstallString": "C:\\OrkGame\\uninstall.exe",
        })
    ]
    with patch_wrc(subkeys):
        finder = WindowsAppFinder()
        finder.refresh()
        assert None == finder._match_uninstall_key(human_name)


def test_find_game_display_icon(uk_torchlight2):
    """Find exe based on DisplayIcon subkey"""
    human_name, machine_name = "Torchlight 2", "torchlight2"
    finder = WindowsAppFinder()
    location = pathlib.PurePath(uk_torchlight2.display_icon).parent
    expected = pathlib.Path(uk_torchlight2.display_icon)
    with patch.object(finder._reg, '_WindowsRegistryClient__uninstall_keys', [uk_torchlight2]):
        with patch('pathlib.Path.exists', lambda path: location in path.parents):
            assert expected == finder.find_local_game(machine_name, human_name).executable


def test_find_game_display_uninstall():
    """Find exe based on DisplayIcon subkey but not if it is uninstaller"""
    human_name = "Agame"
    uninstall = "C:\\agame\\uninstall.exe"
    uk_game = UninstallKey(
        key_name=human_name,
        display_name=human_name,
        uninstall_string=uninstall,
        _display_icon=uninstall
    )
    finder = WindowsAppFinder()
    with patch.object(finder._reg, '_WindowsRegistryClient__uninstall_keys', [uk_game]):
        # not existing path
        assert None == finder.find_local_game(human_name, human_name)