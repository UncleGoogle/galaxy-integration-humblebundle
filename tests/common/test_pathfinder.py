import pytest
from unittest import mock
from pathlib import Path

from local.pathfinder import PathFinder
from consts import HP


# ------------ find_executables -----------------

@pytest.fixture()
def s1_dir_exe():
    return [
        ('StarCraft', ('editor',), ('Starcraft.exe',)),
        ('StarCraft\\editor', (), ('logs.logs', 'editor.exe')),
    ]


@pytest.fixture()
def s1_dir_no_exe():
    return [
        ('StarCraft', ('editor',), ('Starcraft',)),
        ('StarCraft\\editor', (), ('logs.logs', 'editor')),
    ]

@pytest.fixture()
def s1_dir_exe_mac():
    return [
        ('StarCraft', ('editor',), ('Starcraft',)),
        ('StarCraft/editor', (), ('logs.logs', 'editor')),
    ]


@mock.patch('os.walk')
@mock.patch.object(Path, 'exists', (lambda _: True))
def test_find_exec_win_empty(mock_walk, s1_dir_no_exe):
    mock_walk.return_value = s1_dir_no_exe
    execs = PathFinder(HP.WINDOWS).find_executables('some_mock_path')
    assert execs == []


@mock.patch('os.walk')
@mock.patch.object(Path, 'exists', (lambda _: True))
def test_find_exec_win(mock_walk, s1_dir_exe):
    mock_walk.return_value = s1_dir_exe
    execs = PathFinder(HP.WINDOWS).find_executables('some_mock_path')
    assert execs == ['StarCraft\\Starcraft.exe', 'StarCraft\\editor\\editor.exe']


@mock.patch('os.walk')
@mock.patch('os.path.join', (lambda x, y: '/'.join([x, y])))
@mock.patch.object(Path, 'exists', (lambda _: True))
def test_find_exec_mac(mock_walk, s1_dir_exe_mac):

    def define_execs(execs):
        def mock_access(path, _):
            return path in execs
        return mock_access

    expected = ['StarCraft/Starcraft', 'StarCraft/editor/editor']
    with mock.patch('os.access', define_execs(expected)):
        mock_walk.return_value = s1_dir_exe_mac
        execs = PathFinder(HP.MAC).find_executables('some_mock_path')
        assert execs == expected


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

def test_choose_full_path():
    app_name = "Anna's Quest"
    expected = 'C:\\Games\\AnnasQuest\\anna.exe'
    executables = ['C:\\Games\\AnnasQuest\\uninst.exe', expected]
    res = PathFinder.choose_main_executable(app_name, executables)
    assert res == expected

def test_choose_legendary_heroes():
    app_name = "Fallen Enchantress: Legendary Heroes"
    executables = [
        'C:\\Users\\me\\humblebundle\\DataZip.exe',
        'C:\\Users\\me\\humblebundle\\DXAtlasWin.exe',
        'C:\\Users\\me\\humblebundle\\LegendaryHeroes.exe',
        'C:\\Users\\me\\humblebundle\\LH_prefs_setup.exe'
    ]
    expected = executables[2]
    res = PathFinder.choose_main_executable(app_name, executables)
    assert res == expected