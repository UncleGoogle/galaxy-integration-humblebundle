import pytest
import pathlib
from unittest.mock import patch, PropertyMock
from contextlib import contextmanager

from local._winappfinder import WindowsRegistryClient, UninstallKey, WindowsAppFinder
from humblegame import TroveGame


@pytest.fixture
def patch_wrc():
    @contextmanager
    def fn(subkeys):
        def mock_get_val(subkey, prop, optional=False):
            if optional:
                return subkey.get(prop)
            return subkey[prop]

        with patch.object(WindowsRegistryClient, "_iterate_new_uninstall_keys") as subkey_gen, \
             patch.object(WindowsRegistryClient, "_WindowsRegistryClient__get_value") as get_val:
            subkey_gen.return_value = iter(subkeys)
            get_val.side_effect = mock_get_val
            yield
    return fn


@pytest.fixture
def uk_annas_quest():
    return UninstallKey(
        key_name="Anna's Quest_is1",
        display_name="Anna's Quest",
        uninstall_string="\"D:\\Games\\Anna's Quest\\unins000.exe\"",
        _install_location="D:\\Games\\Anna's Quest\\",
    )


@pytest.fixture
def uk_windosill():
    return UninstallKey(
        key_name="Windosill_is1",
        display_name= "Windosill version 1.61",
        uninstall_string="\"C:\\Games\\The Windosill\\uninstall.exe\"",
        _install_location="C:\\Games\\The Windosill\\"
    )


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


# --------- WinRegClient ---------------

def test_refresh_uks(uk_annas_quest, uk_windosill, patch_wrc):
    human_name = "Anna's Quest"
    subkeys = [
        ("Anna's Quest_is1", {
        "DisplayName": "Anna's Quest",
        "InstallLocation": "D:\\Games\\Anna's Quest\\",
        "UninstallString": "\"D:\\Games\\Anna's Quest\\unins000.exe\""
        }),
        (uk_windosill.key_name, {
            "DisplayName": uk_windosill.display_name,
            "InstallLocation": uk_windosill._install_location,
            "UninstallString": uk_windosill.uninstall_string
        })
    ]
    expected = set([uk_annas_quest, uk_windosill])
    with patch_wrc(subkeys):
        finder = WindowsAppFinder()
        finder.refresh()
        assert finder._reg.uninstall_keys == expected

# --------- WindowsAppFinder -----------

def test_match_by_key_name():
    uk = UninstallKey('Limbo', '', uninstall_string='')
    human_name = 'LIMBO'
    assert True == WindowsAppFinder._matches(human_name, uk)

def test_match_with_folder_name():
    human_name = "The Windosill"
    install_location = 'C:\\Games\\The Windosill\\'
    uk = UninstallKey(
        key_name="Windosill_is1",
        display_name="Windosill version 1.61",
        uninstall_string="\"C:\\Games\\The Windosill\\uninstall.exe\"",
        _install_location=install_location,
    )
    assert True == WindowsAppFinder._matches(human_name, uk)


def test_match_colon_in_name():
    human_name = "Orks: final cutdown"
    install_location = "C:\\Games\\Orks Final Cutdown"
    uk = UninstallKey(
        key_name="mock",
        display_name="Orks Final Cutdown",
        uninstall_string="mock",
        _install_location=install_location,
    )
    assert True == WindowsAppFinder._matches(human_name, uk)


def test_no_match():
    human_name = "Orks: final cutdown"
    uk = UninstallKey(
        'keyname',
        'displayname',
        'uninstall_str',
        _install_location='somewhere\\else',
    )
    assert False == WindowsAppFinder._matches(human_name, uk)


# ------------ find local games

def test_find_games_display_icon(uk_torchlight2):
    """Find exe based on DisplayIcon subkey"""
    human_name, machine_name = "Torchlight 2", "torchlight2"
    owned_games = [TroveGame({'human-name': human_name, 'machine_name': machine_name})]
    finder = WindowsAppFinder()
    expected_exe = uk_torchlight2.display_icon
    with patch.object(finder._reg, '_WindowsRegistryClient__uninstall_keys', [uk_torchlight2]):
        with patch('pathlib.Path.exists', lambda path: location in path.parents):
            assert expected_exe == finder.find_local_games(owned_games)[0].executable


def test_find_game_display_uninstall():
    """Find exe based on DisplayIcon subkey but not if it is uninstaller"""
    human_name, machine_name = "Agame", 'agame'
    uninstall = "C:\\agame\\uninstall.exe"
    uk_game = UninstallKey(
        key_name=human_name,
        display_name=human_name,
        uninstall_string=uninstall,
        _display_icon=uninstall
    )
    owned_games = [TroveGame({'human-name': human_name, 'machine_name': machine_name})]
    finder = WindowsAppFinder()
    with patch.object(finder._reg, '_WindowsRegistryClient__uninstall_keys', set([uk_game])):
        assert [] == finder.find_local_games(owned_games)