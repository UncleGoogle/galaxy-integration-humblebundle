import pytest
from pathlib import Path

from local import AppFinder
from local.baseappfinder import GameLocation
from consts import IS_WINDOWS


# unit

@pytest.fixture
def candidates():
    """Bunch of owned game names that are candidates for matching algorithm"""
    return set(
        ['Dummy', 'Haven Moon - DRM free', 'Trine 2: Complete Story', 'Space Pilgrim Episode III: Delta Pavonis', 'Halcyon 6: LIGHTSPEED EDITION', 'Shank 2', 'AaaaaAAaaaAAAaaAAAAaAAAAA!!! for the Awesome']
    )


@pytest.mark.parametrize('dirname, expected', [
    ('Dummy', ['Dummy']),
    ('Haven Moon - DRM free', ['Haven Moon - DRM free']),
])
def test_get_close_matches_exact(dirname, expected, candidates):
    result = AppFinder().get_close_matches(dirname, candidates, similarity=1)
    assert expected == result


@pytest.mark.parametrize('dirname, expected', [
    ('Dummy', ['Dummy']),
    ('Trine 2 Complete Story', ['Trine 2: Complete Story']),
])
def test_get_close_matches_close(dirname, expected, candidates):
    result = AppFinder().get_close_matches(dirname, candidates, similarity=0.8)
    assert expected == result

# integration

@pytest.fixture
def create_tmp_tree():
    def fn(paths):
        """
        :param paths: iterable of os.walk-like tuples
        """
        for root, dirs, files in paths:
            root.mkdir(exist_ok=True)
            for d in dirs:
                (root / d).mkdir()
            for f in files:
                (root / f).touch()
        return root
    return fn


@pytest.mark.skipif(not IS_WINDOWS, reason="windows case")
@pytest.mark.asyncio
async def test_scan_folder_windows(create_tmp_tree, tmp_path):
    root = tmp_path
    create_tmp_tree([
        (root, ('Samorost2', 'Shelter'), ()),
        (root / 'Samorost2', ('01intro', '02pokop'), ('Samorost2.exe', 'Samorost2.ico')),
        (root / 'Shelter', ('bin', 'assets'), ('Shelter.exe', 'README.txt'))
    ])

    owned_games = {'Shelter'}
    result = await AppFinder()._scan_folders([root], owned_games)
    root_shelter = Path(root) / 'Shelter'
    assert {'Shelter': GameLocation(root_shelter, root_shelter / 'Shelter.exe')} == result

    owned_games = {'Samorost 2'}
    result = await AppFinder()._scan_folders([root], owned_games)
    root_samorost = Path(root) / 'Samorost2'
    assert {'Samorost 2': GameLocation(root_samorost, root_samorost / 'Samorost2.exe')} == result

    owned_games = {'Samorost 2', 'Shelter'}
    assert {
        'Samorost 2': GameLocation(root_samorost, root_samorost / 'Samorost2.exe'),
        'Shelter': GameLocation(root_shelter, root_shelter / 'Shelter.exe')
    } == await AppFinder()._scan_folders([root], owned_games)
