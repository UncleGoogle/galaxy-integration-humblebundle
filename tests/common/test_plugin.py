import pytest
from unittest.mock import patch, Mock, PropertyMock
import pathlib

from galaxy.api.consts import OSCompatibility as OSC
from galaxy.api.types import GameLibrarySettings

from consts import HP, CURRENT_SYSTEM
from local.localgame import LocalHumbleGame
from model.game import Subproduct, KeyGame, TroveGame
from model.download import TroveDownload


@pytest.mark.asyncio
async def test_launch_game(plugin, overgrowth):
    id_ = overgrowth['product']['machine_name']
    plugin._local_games = {
        id_: LocalHumbleGame(id_, pathlib.Path('game_dir') /  'mock.exe')
    }
    with patch('subprocess.Popen') as subproc:
        with patch('psutil.Process'):
            await plugin.launch_game(id_)
            if CURRENT_SYSTEM == HP.WINDOWS:
                subproc.assert_called_once_with('game_dir\\mock.exe', creationflags=8 ,cwd=pathlib.Path('game_dir'))
            elif CURRENT_SYSTEM == HP.MAC:
                subproc.assert_called_once()


@pytest.mark.asyncio
async def test_uninstall_game(plugin, overgrowth):
    id_ = overgrowth['product']['machine_name']
    plugin._local_games = {
        id_: LocalHumbleGame(id_, '', uninstall_cmd="unins000.exe")
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
async def test_install_game_trove(api_mock, plugin):
    id_ = 'trove_game'
    game = Mock(spec=TroveGame, downloads={CURRENT_SYSTEM: Mock(spec=TroveDownload)})
    plugin._owned_games = { id_: game }
    expected_url = "https://dl.humble.com/developer/trove_game_012_build-5584-win64.zip?gamekey=XrCTukcAFwsh&ttl=1563893021&t=7f2263e7f3360f3beb112e58521145a0"
    api_mock.sign_url_trove.return_value = {
        "signed_url": expected_url
    }

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
    plugin._owned_games= { ovg_id: game, no_downloads_id: no_dw_game}

    ctx = await plugin.prepare_os_compatibility_context([ovg_id, no_downloads_id])
    assert await plugin.get_os_compatibility(no_downloads_id, ctx) == None
    assert await plugin.get_os_compatibility(ovg_id, ctx) == OSC.Windows | OSC.MacOS | OSC.Linux


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
