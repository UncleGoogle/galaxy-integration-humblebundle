import pathlib

import pytest

from local.localgame import LocalHumbleGame


@pytest.fixture
def create_file_at():
    def fn(path: pathlib.Path, content: bytes) -> int:
        path.parent.mkdir(exist_ok=True, parents=True)
        size = path.write_bytes(content)
        return size
    return fn


@pytest.mark.asyncio
async def test_get_size_not_root(tmp_path, create_file_at):
    game_root = tmp_path / 'root'
    expected_size = sum([
        create_file_at(game_root / 'bin' / 'game.exe', b'exe_content'),
        create_file_at(game_root / 'assets' / 'data0.dat', b'data/32\fxxxxxxx'),
        create_file_at(game_root / 'assets' / 'data1.dat', b'da/32')
    ])
    create_file_at(tmp_path / 'another_dir' / 'exe', b'00000xxxx')  # do not count this

    game = LocalHumbleGame('mock', tmp_path / 'bin' / 'game.exe', install_location=game_root)
    assert await game.get_size() == expected_size


@pytest.mark.asyncio
async def test_get_size_no_install_location(tmp_path, create_file_at):
    """Executable parent should be inspected as install dir as most reasonable fallback"""
    expected_size = sum([
        create_file_at(tmp_path / 'game.exe', b'exe_content'),
        create_file_at(tmp_path / 'assets' / 'data0.dat', b'data/32\fxxxxxxx'),
        create_file_at(tmp_path / 'assets' / 'data1.dat', b'da/32')
    ])
    game = LocalHumbleGame('mock', tmp_path / 'game.exe', install_location=None)
    assert await game.get_size() == expected_size
