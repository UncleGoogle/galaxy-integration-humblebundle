import pytest
from unittest.mock import patch, Mock, PropertyMock
import pathlib

from galaxy.api.consts import OSCompatibility as OSC
from galaxy.api.types import GameLibrarySettings

from consts import IS_WINDOWS, IS_MAC
from local.localgame import LocalHumbleGame
from model.game import Subproduct, KeyGame, TroveGame, ChoiceGame

from conftest import AsyncMock


@pytest.mark.asyncio
async def test_launch_game(plugin, overgrowth):
    id_ = overgrowth['product']['machine_name']
    plugin._local_games = {
        id_: LocalHumbleGame(id_, pathlib.Path('game_dir') /  'mock.exe')
    }
    with patch('subprocess.Popen') as subproc:
        with patch('psutil.Process'):
            await plugin.launch_game(id_)
            if IS_WINDOWS:
                subproc.assert_called_once_with('game_dir\\mock.exe', creationflags=8 ,cwd=pathlib.Path('game_dir'))
            elif IS_MAC:
                subproc.assert_called_once()


@pytest.mark.asyncio
async def test_uninstall_game(plugin, overgrowth):
    id_ = overgrowth['product']['machine_name']
    plugin._local_games = {
        id_: LocalHumbleGame(id_, Mock(), uninstall_cmd="unins000.exe")
    }
    with patch('subprocess.Popen') as subproc:
        await plugin.uninstall_game(id_)
        subproc.assert_called_once_with('unins000.exe')


@pytest.mark.asyncio
async def test_install_game_drm_free(api_mock, plugin, overgrowth):
    id_ = overgrowth['product']['machine_name']
    subproduct = overgrowth['subproducts'][0]
    game = Subproduct(subproduct)
    plugin._owned_games = { id_: game }
    expected_url = "https://dl.humble.com/wolfiregames/overgrowth-1.4.0_build-5584-win64.zip?gamekey=XrCTukcAFwsh&ttl=1563893021&t=7f2263e7f3360f3beb112e58521145a0"
    api_mock.sign_url_subproduct.return_value = {
        "signed_url": expected_url
    }

    with patch('webbrowser.open') as browser_open:
        await plugin.install_game(id_)
        browser_open.assert_called_once_with(expected_url)


@pytest.mark.asyncio
async def test_install_game_choice(plugin):
    id_ = 'game_id'
    game = ChoiceGame(id_, 'The Game', 'may_2020')
    plugin._choice_games = { id_: game }
    expected_url = 'https://www.humblebundle.com/subscription/may_2020/game_id'
    with patch('webbrowser.open') as browser_open:
        await plugin.install_game(id_)
        browser_open.assert_called_once_with(expected_url)


@pytest.mark.asyncio
async def test_install_game_choice_extras(plugin):
    """
    For extrases we just show subscription month url.
    If extras comes from unlocked month, it should be in owned_games as well in form of Key or Subproduct.
    In such case direct download is possible from different game page view.
    """
    id_ = 'game_id'
    game = ChoiceGame(id_, 'The Game DLC1', 'may_2020', is_extras=True)
    plugin._choice_games = { id_: game }
    expected_url = 'https://www.humblebundle.com/subscription/may_2020'
    with patch('webbrowser.open') as browser_open:
        await plugin.install_game(id_)
        browser_open.assert_called_once_with(expected_url)


@pytest.mark.asyncio
async def test_get_os_compatibility(plugin, overgrowth):
    ovg_id = overgrowth['product']['machine_name']
    subproduct = overgrowth['subproducts'][0]
    game = Subproduct(subproduct)

    no_downloads_id = 'nodw'
    no_dw_game = Subproduct({
        'human_name': 'mock',
        'machine_name': no_downloads_id,
        'downloads': []
    })

    key_game_id = 'keyg'
    key_game = Mock(spec=KeyGame)

    plugin._owned_games = {
        ovg_id: game,
        no_downloads_id: no_dw_game,
        key_game_id: key_game
    }

    ctx = await plugin.prepare_os_compatibility_context(plugin._owned_games.keys())
    assert await plugin.get_os_compatibility(no_downloads_id, ctx) == None
    assert await plugin.get_os_compatibility(ovg_id, ctx) == OSC.Windows | OSC.MacOS | OSC.Linux
    assert await plugin.get_os_compatibility(key_game_id, ctx) == OSC.Windows | OSC.MacOS | OSC.Linux


@pytest.mark.asyncio
async def test_library_settings_key(plugin):
    trove = Mock(spec=TroveGame)
    drm_free = Mock(spec=Subproduct)
    key = Mock(spec=KeyGame)
    type(key).key_val = PropertyMock(return_value='COEO23DN')
    unrevealed_key = Mock(spec=KeyGame)
    type(unrevealed_key).key_val = PropertyMock(return_value=None)

    plugin._owned_games = {
        'a': drm_free,
        'b': trove,
        'c': key,
        'd': unrevealed_key
    }

    ctx = await plugin.prepare_game_library_settings_context(['b', 'c', 'd', 'a'])
    assert await plugin.get_game_library_settings('a', ctx) == GameLibrarySettings('a', None, None)
    assert await plugin.get_game_library_settings('b', ctx) == GameLibrarySettings('b', [], None)
    assert await plugin.get_game_library_settings('c', ctx) == GameLibrarySettings('c', ['Key'], None)
    assert await plugin.get_game_library_settings('d', ctx) == GameLibrarySettings('d', ['Key', 'Unrevealed'], None)


@pytest.mark.asyncio
async def test_local_size(plugin):
    local_game_mock = Mock(spec=LocalHumbleGame)
    local_game_mock.get_size = AsyncMock(return_value=100200300)
    plugin._local_games = {
        'loc': local_game_mock
    }
    ctx = await plugin.prepare_local_size_context(['loc'])
    assert await plugin.get_local_size('loc', ctx) == 100200300
