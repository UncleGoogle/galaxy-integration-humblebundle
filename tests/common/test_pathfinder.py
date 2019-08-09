import pytest
from unittest import mock
from pathlib import Path, PureWindowsPath, PurePosixPath

from local.pathfinder import PathFinder
from consts import HP, CURRENT_SYSTEM


# ------------ find_executables -----------------

@pytest.fixture()
def s1_dir_exe():
    return [
        ('StarCraft', ('editor',), ('Starcraft.exe',)),
        (str(PureWindowsPath('StarCraft') / 'editor'), (), ('logs.logs', 'editor.exe')),
    ]


@pytest.fixture()
def s1_dir_no_exe():
    return [
        ('StarCraft', ('editor',), ('Starcraft',)),
        (str(PureWindowsPath('StarCraft') / 'editor'), (), ('logs.logs', 'editor')),
    ]

@pytest.fixture()
def s1_dir_exe_mac():
    return [
        ('StarCraft', ('editor',), ('Starcraft',)),
        (str(PurePosixPath('StarCraft') / 'editor'), (), ('logs.logs', 'editor')),
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
    assert execs == [str(Path('StarCraft') / 'Starcraft.exe'), str(Path('StarCraft') / 'editor' / 'editor.exe')]


@mock.patch('os.walk')
@mock.patch('os.path.join', (lambda x, y: '/'.join([x, y])))
@mock.patch.object(Path, 'exists', (lambda _: True))
def test_find_exec_mac(mock_walk, s1_dir_exe_mac):

    def define_execs(execs):
        def mock_access(path, _):
            return path in execs
        return mock_access

    expected = [str(PurePosixPath('StarCraft') / 'Starcraft'), str(PurePosixPath('StarCraft') / 'editor' / 'editor')]
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
    expected = PureWindowsPath('C:\\Games\\AnnasQuest\\anna.exe')
    executables = [PureWindowsPath('C:\\Games\\AnnasQuest\\uninst.exe'), expected]

    if CURRENT_SYSTEM == HP.WINDOWS:
        executables = [str(x) for x in executables]
    else:
        executables = [str(x.as_posix()) for x in executables]

    res = PathFinder.choose_main_executable(app_name, executables)
    assert res == str(expected)

def test_choose_legendary_heroes():
    app_name = "Fallen Enchantress: Legendary Heroes"
    executables = [
        PureWindowsPath('C:\\Users\\me\\humblebundle\\DataZip.exe'),
        PureWindowsPath('C:\\Users\\me\\humblebundle\\DXAtlasWin.exe'),
        PureWindowsPath('C:\\Users\\me\\humblebundle\\LegendaryHeroes.exe'),
        PureWindowsPath('C:\\Users\\me\\humblebundle\\LH_prefs_setup.exe')
    ]

    if CURRENT_SYSTEM == HP.WINDOWS:
        executables = [str(x) for x in executables]
    else:
        executables = [str(x.as_posix()) for x in executables]

    expected = executables[2]
    res = PathFinder.choose_main_executable(app_name, executables)
    assert res == expected