import pytest
import asyncio
from unittest.mock import MagicMock

from gui.options import OPTIONS_MODE


@pytest.fixture
def auth_cookie():
    return {
        "name":"_simpleauth_sess",
        "value":"eyJ1c2VyX2lkIjo2MTkyOTY2OTY2mTgxODg4LCJpZCI6IlQ2M2pnU0EzbHEiLCJhdXRoX3RpbWUiOjE1NjY2Njc4NzJ9|1564667873|2bf5bff888a81118e8014af6041a58a2b31c00d6"
    }


@pytest.mark.asyncio
async def test_open_news_on_minor_update(plugin, auth_cookie, mocker):
    plugin._open_config = MagicMock(spec=())
    plugin._last_version = '0.6.1'
    mocker.patch('plugin.__version__', '0.7.0')
    await plugin.authenticate(stored_credentials=auth_cookie)
    plugin._open_config.assert_called_once_with(OPTIONS_MODE.NEWS)


@pytest.mark.asyncio
async def test_do_not_open_news_on_patch_update(plugin, auth_cookie, mocker):
    plugin._open_config = MagicMock(spec=())
    plugin._last_version = '0.7.0'
    mocker.patch('plugin.__version__', '0.7.1')
    await plugin.authenticate(stored_credentials=auth_cookie)
    plugin._open_config.assert_not_called()


@pytest.mark.asyncio
async def test_open_welcome_on_authenticate(plugin, auth_cookie):
    plugin._open_config = MagicMock(spec=())
    await plugin.pass_login_credentials('step', 'credentials', [auth_cookie])
    plugin._open_config.assert_called_once_with(OPTIONS_MODE.WELCOME)


@pytest.mark.asyncio
async def test_open_options_on_clicking_install(plugin, delayed_fn):
    plugin._open_config = MagicMock(spec=())
    await asyncio.gather(
        delayed_fn(0.1, plugin.install_game),
        delayed_fn(0.2, plugin.install_game)
    )
    plugin._open_config.assert_called_once()
