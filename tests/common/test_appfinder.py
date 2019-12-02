import pytest
import os
from pathlib import Path

from local import AppFinder
from consts import IS_WINDOWS


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
