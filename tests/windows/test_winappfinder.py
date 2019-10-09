import pytest
from unittest.mock import patch

try:
    from local.appfinder import WindowsAppFinder
    from local._reg_watcher import UninstallKey
except ModuleNotFoundError:
    pass  # workaround problems in vscode test discovery
from model.game import TroveGame


@pytest.fixture
def uk_torchlight2():
    """In this real example, there is no installLocation and displayIcon links to launcher executable.
    """
    return UninstallKey(
        key_name = "{049FF5E4-EB02-4c42-8DB0-226E2F7A9E53}",
        display_name = "Torchlight 2",
        uninstall_string = R"C:\Users\Public\Games\Runic Games\Torchlight 2\uninstall.exe",
        install_location = None,
        display_icon = R"C:\Users\Public\Games\Runic Games\Torchlight 2\ModLauncher.exe",
    )


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
        install_location=install_location,
    )
    assert True == WindowsAppFinder._matches(human_name, uk)


def test_match_colon_in_name():
    human_name = "Orks: final cutdown"
    install_location = "C:\\Games\\Orks Final Cutdown"
    uk = UninstallKey(
        key_name="mock",
        display_name="Orks Final Cutdown",
        uninstall_string="mock",
        install_location=install_location,
    )
    assert True == WindowsAppFinder._matches(human_name, uk)


def test_no_match():
    human_name = "Orks: final cutdown"
    uk = UninstallKey(
        'keyname',
        'displayname',
        'uninstall_str',
        install_location='somewhere\\else',
    )
    assert False == WindowsAppFinder._matches(human_name, uk)


# ------------ find local games ---------

@pytest.mark.asyncio
async def test_find_games_display_icon(uk_torchlight2):
    """Find exe based on DisplayIcon subkey"""
    human_name, machine_name = "Torchlight 2", "torchlight2"
    owned_games = {human_name: machine_name}
    finder = WindowsAppFinder()
    expected_exe = uk_torchlight2.display_icon
    with patch.object(finder._reg, '_WinRegUninstallWatcher__uninstall_keys', [uk_torchlight2]):
        res = await finder.find_local_games(owned_games, [])
        assert machine_name in res
        assert expected_exe == str(res[machine_name].executable)


@pytest.mark.asyncio
async def test_find_game_display_uninstall():
    """Find exe based on DisplayIcon subkey but not if it is uninstaller"""
    human_name, machine_name = "Agame", 'agame'
    uninstall = "C:\\agame\\uninstall.exe"
    uk_game = UninstallKey(
        key_name=human_name,
        display_name=human_name,
        uninstall_string=uninstall,
        display_icon=uninstall
    )
    owned_games = {human_name: machine_name}
    finder = WindowsAppFinder()
    with patch.object(finder._reg, '_WinRegUninstallWatcher__uninstall_keys', set([uk_game])):
        assert {} == await finder.find_local_games(owned_games, [])