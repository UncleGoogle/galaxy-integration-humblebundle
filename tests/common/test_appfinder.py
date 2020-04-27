import pytest
import os
from pathlib import Path

from local import AppFinder
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


@pytest.mark.skipif(not IS_WINDOWS, reason="windows case")
@pytest.mark.asyncio
async def test_scan_folder_windows(create_mock_walk):
    root = 'C:\\Program Files (x86)'
    paths = [
        (root, ('Samorost2', 'Shelter'), ()),
        (root + os.sep + 'Samorost2', ('01intro', '02pokop'), ('Samorost2.exe', 'Samorost2.ico')),
        (root + os.sep + 'Shelter', ('bin', 'assets'), ('Shelter.exe', 'README.txt'))
    ]
    create_mock_walk(paths)

    owned_games = {'Shelter'}
    result = await AppFinder()._scan_folders([root], owned_games)
    assert {'Shelter': Path(root) / 'Shelter' / 'Shelter.exe'} == result

    owned_games = {'Samorost 2'}
    result = await AppFinder()._scan_folders([root], owned_games)
    assert {'Samorost 2': Path(root) / 'Samorost2' / 'Samorost2.exe'} == result

    owned_games = {'Samorost 2', 'Shelter'}
    assert {
        'Samorost 2': Path(root) / 'Samorost2' / 'Samorost2.exe',
        'Shelter': Path(root) / 'Shelter' / 'Shelter.exe'
    } == await AppFinder()._scan_folders([root], owned_games)
