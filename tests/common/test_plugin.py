import pytest
from unittest.mock import patch, Mock, PropertyMock
import pathlib

from galaxy.api.consts import OSCompatibility as OSC
from galaxy.api.types import GameLibrarySettings

from consts import HP, CURRENT_SYSTEM
from local.localgame import LocalHumbleGame
from model.game import Subproduct, KeyGame, TroveGame
from humbledownloader import HumbleDownloadResolver


@pytest.mark.asyncio
async def test_launch_game(plugin_mock, overgrowth):
    id_ = overgrowth['product']['machine_name']
    plugin_mock._local_games = {
        id_: LocalHumbleGame(id_, pathlib.Path('game_dir') /  'mock.exe')
    }
    with patch('subprocess.Popen') as subproc:
        with patch('psutil.Process'):
            await plugin_mock.launch_game(id_)
            if CURRENT_SYSTEM == HP.WINDOWS:
                subproc.assert_called_once_with('game_dir\\mock.exe', creationflags=8 ,cwd=pathlib.Path('game_dir'))
            elif CURRENT_SYSTEM == HP.MAC:
                subproc.assert_called_once()


@pytest.mark.asyncio
async def test_uninstall_game(plugin_mock, overgrowth):
    id_ = overgrowth['product']['machine_name']
    plugin_mock._local_games = {
        id_: LocalHumbleGame(id_, '', uninstall_cmd="unins000.exe")
    }
    with patch('subprocess.Popen') as subproc:
        await plugin_mock.uninstall_game(id_)
        subproc.assert_called_once_with('unins000.exe')


@pytest.mark.asyncio
@pytest.mark.parametrize('os_', [HP.WINDOWS, HP.MAC])
async def test_install_game(os_, api_mock, plugin_mock, overgrowth):
    id_ = overgrowth['product']['machine_name']
    subproduct = overgrowth['subproducts'][0]
    game = Subproduct(subproduct, overgrowth['gamekey'])
    plugin_mock._owned_games = { id_: game }
    # Note windows have also download_struct named "Patch". Not supported currently, only one download
    download_urls = {
        "linux": "https://dl.humble.com/wolfiregames/overgrowth-1.4.0_build-5584-linux64.zip?gamekey=XrCTukcAFwsh&ttl=1563893021&t=46b9a84ac7c864cf8fe263239a9978ae",
        "windows": "https://dl.humble.com/wolfiregames/overgrowth-1.4.0_build-5584-win64.zip?gamekey=XrCTukcAFwsh&ttl=1563893021&t=7f2263e7f3360f3beb112e58521145a0",
        "mac": "https://dl.humble.com/wolfiregames/overgrowth-1.4.0_build-5584-macosx.zip?gamekey=XrCTukcAFwsh&ttl=1563893021&t=5ade7954d8fc63bbe861932be538c07e",
    }

    plugin_mock._download_resolver = HumbleDownloadResolver(target_platform=os_)
    with patch('webbrowser.open') as browser_open:
        await plugin_mock.install_game(id_)
        browser_open.assert_called_once_with(download_urls[os_.value])


@pytest.mark.asyncio
async def test_get_os_compatibility(plugin_mock, overgrowth):
    ovg_id = overgrowth['product']['machine_name']
    subproduct = overgrowth['subproducts'][0]
    game = Subproduct(subproduct, overgrowth['gamekey'])

    no_downloads_id = 'nodw'
    no_dw_game = Subproduct({
        'human_name': 'mock',
        'machine_name': no_downloads_id,
        'downloads': []
    }, 'mock')
    plugin_mock._owned_games= { ovg_id: game, no_downloads_id: no_dw_game}

    ctx = await plugin_mock.prepare_os_compatibility_context([ovg_id, no_downloads_id])
    assert await plugin_mock.get_os_compatibility(no_downloads_id, ctx) == None
    assert await plugin_mock.get_os_compatibility(ovg_id, ctx) == OSC.Windows | OSC.MacOS | OSC.Linux


@pytest.mark.asyncio
async def test_library_settings_key(plugin_mock):
    trove = Mock(spec=TroveGame)
    drm_free = Mock(spec=Subproduct)
    key = Mock(spec=KeyGame)
    type(key).key_val = PropertyMock(return_value='COEO23DN')
    unrevealed_key = Mock(spec=KeyGame)
    type(unrevealed_key).key_val = PropertyMock(return_value=None)

    plugin_mock._owned_games = {
        'a': drm_free,
        'b': trove,
        'c': key,
        'd': unrevealed_key
    }

    ctx = await plugin_mock.prepare_game_library_settings_context(['b', 'c', 'd', 'a'])
    assert await plugin_mock.get_game_library_settings('a', ctx) == GameLibrarySettings('a', None, None)
    assert await plugin_mock.get_game_library_settings('b', ctx) == GameLibrarySettings('b', ['Trove'], None)
    assert await plugin_mock.get_game_library_settings('c', ctx) == GameLibrarySettings('c', ['Key'], None)
    assert await plugin_mock.get_game_library_settings('d', ctx) == GameLibrarySettings('d', ['Key', 'Unrevealed'], None)
