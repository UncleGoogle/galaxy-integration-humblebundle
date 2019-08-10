import pytest
from unittest.mock import patch
import pathlib

from consts import HP
from local.localgame import LocalHumbleGame
from humblegame import Subproduct
from humbledownloader import HumbleDownloadResolver


@pytest.mark.asyncio
async def test_launch_game(plugin_mock, overgrowth):
    id_ = overgrowth['product']['machine_name']
    plugin_mock._local_games = {
        id_: LocalHumbleGame(id_, pathlib.Path('mock.exe'))
    }
    with patch('subprocess.Popen') as subproc:
        with patch('psutil.Process'):
            await plugin_mock.launch_game(id_)
            subproc.assert_called_once_with('mock.exe')


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
async def test_install_game(plugin_mock, overgrowth):
    id_ = overgrowth['product']['machine_name']
    subproduct = overgrowth['subproducts'][0]

    game = Subproduct(subproduct)
    plugin_mock._owned_games= { id_: game }
    # Note windows have also download_struct named "Patch". Not supported currently, only one download
    download_urls = {
        "linux": "https://dl.humble.com/wolfiregames/overgrowth-1.4.0_build-5584-linux64.zip?gamekey=XrCTukcAFwsh&ttl=1563893021&t=46b9a84ac7c864cf8fe263239a9978ae",
        "windows": "https://dl.humble.com/wolfiregames/overgrowth-1.4.0_build-5584-win64.zip?gamekey=XrCTukcAFwsh&ttl=1563893021&t=7f2263e7f3360f3beb112e58521145a0",
        "mac": "https://dl.humble.com/wolfiregames/overgrowth-1.4.0_build-5584-macosx.zip?gamekey=XrCTukcAFwsh&ttl=1563893021&t=5ade7954d8fc63bbe861932be538c07e",
    }

    for os in [HP.WINDOWS, HP.MAC]:
        plugin_mock._download_resolver = HumbleDownloadResolver(target_platform=os)
        with patch('webbrowser.open') as browser_open:
            await plugin_mock.install_game(id_)
            browser_open.assert_called_once_with(download_urls[os.value])