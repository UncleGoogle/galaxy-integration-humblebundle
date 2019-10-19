import pytest
import os
from pathlib import PureWindowsPath, Path

from local.pathfinder import PathFinder
from consts import HP, CURRENT_SYSTEM


@pytest.fixture
def systemize():
    def fn(executables):
        if CURRENT_SYSTEM == HP.WINDOWS:
            new_execs = [str(x) for x in executables]
        else:
            new_execs = [str(x.as_posix()) for x in executables]
        return new_execs
    return fn

# ------------ find_executables -----------------

# ---------- choose_main_executable -------------

def test_choose_1exe():
    app_name = "Wildcharts"
    executables = ['game.exe']
    res = PathFinder.choose_main_executable(app_name, executables)
    assert res == executables[0]

def test_choose_exact_match():
    app_name = "The Game"
    executables = ['the game.exe', 'map_editor.exe']
    res = PathFinder.choose_main_executable(app_name, executables)
    assert res == 'the game.exe'

def test_choose_icase():
    app_name = "LIMBO"
    executables = ['limbo.exe', 'other.exe', 'unst000.exe', 'LIM-editor.exe']
    res = PathFinder.choose_main_executable(app_name, executables)
    assert res == 'limbo.exe'

def test_choose_2exe():
    app_name = "Anna's Quest"
    executables = ['anna.exe', 'uninst.exe']
    res = PathFinder.choose_main_executable(app_name, executables)
    assert res == 'anna.exe'

def test_choose_full_path(systemize):
    app_name = "Anna's Quest"
    executables = [
        PureWindowsPath('C:\\Games\\AnnasQuest\\uninst.exe'),
        PureWindowsPath('C:\\Games\\AnnasQuest\\anna.exe')
    ]
    executables = systemize(executables)
    expected = executables[1]

    res = PathFinder.choose_main_executable(app_name, executables)
    assert res == str(expected)

def test_choose_legendary_heroes(systemize):
    app_name = "Fallen Enchantress: Legendary Heroes"
    executables = [
        PureWindowsPath('C:\\Users\\me\\humblebundle\\DataZip.exe'),
        PureWindowsPath('C:\\Users\\me\\humblebundle\\DXAtlasWin.exe'),
        PureWindowsPath('C:\\Users\\me\\humblebundle\\LegendaryHeroes.exe'),
        PureWindowsPath('C:\\Users\\me\\humblebundle\\LH_prefs_setup.exe')
    ]
    executables = systemize(executables)
    expected = executables[2]

    res = PathFinder.choose_main_executable(app_name, executables)
    assert res == expected

# ---------- scan folders -------------

@pytest.fixture
def create_mock_walk(mocker):
    def fn(walk_paths: list):
        """ Creates mock of os.walk that is a bit more inteligent than simple return_value = iter(...)
        Also patch Path exists to True
        paths - expected os.walk result as a list of tuples
        """
        mocker.patch.object(Path, 'exists', return_value=True)
        mock_walk = mocker.patch('os.walk')
        def side_effect(_):
            """self reseting generator"""
            counter = 0
            while True:
                try:
                    yield walk_paths[counter]
                    counter += 1
                except IndexError:
                    counter = 0
                    return
        mock_walk.side_effect = side_effect
        return mock_walk
    return fn


@pytest.mark.asyncio
async def test_scan_folder_windows(create_mock_walk):
    if CURRENT_SYSTEM != HP.WINDOWS:
        return

    root = 'C:\\Program Files (x86)'
    paths = [
        (root, ('Samorost2', 'Shelter'), ()),
        (root + os.sep + 'Samorost2', ('01intro', '02pokop'), ('Samorost2.exe', 'Samorost2.ico')),
        (root + os.sep + 'Shelter', ('bin', 'assets'), ('Shelter.exe', 'README.txt'))
    ]
    create_mock_walk(paths)

    owned_games = {'Shelter'}
    result = await PathFinder(HP.WINDOWS).scan_folders([root], owned_games)
    assert {'Shelter': Path(root) / 'Shelter' / 'Shelter.exe'} == result

    owned_games = {'Samorost 2'}
    result = await PathFinder(HP.WINDOWS).scan_folders([root], owned_games)
    assert {'Samorost 2': Path(root) / 'Samorost2' / 'Samorost2.exe'} == result

    owned_games = {'Samorost 2', 'Shelter'}
    assert {
        'Samorost 2': Path(root) / 'Samorost2' / 'Samorost2.exe',
        'Shelter': Path(root) / 'Shelter' / 'Shelter.exe'
    } == await PathFinder(HP.WINDOWS).scan_folders([root], owned_games)
