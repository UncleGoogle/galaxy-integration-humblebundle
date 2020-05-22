import pytest
from pathlib import PureWindowsPath

from local.pathfinder import PathFinder
from consts import IS_WINDOWS


@pytest.fixture
def systemize():
    def fn(executables):
        if IS_WINDOWS:
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
