import pytest
import asyncio
from unittest.mock import MagicMock

from guirunner import OPTIONS_MODE


@pytest.fixture
def auth_cookie():
    return {
        "name":"_simpleauth_sess",
        "value":"eyJ1c2VyX2lkIjo2MTkyOTY2OTY2mTgxODg4LCJpZCI6IlQ2M2pnU0EzbHEiLCJhdXRoX3RpbWUiOjE1NjY2Njc4NzJ9|1564667873|2bf5bff888a81118e8014af6041a58a2b31c00d6"
    }


@pytest.mark.asyncio
async def test_open_news_on_plugin_update(plugin_mock, auth_cookie, mocker):
    plugin_mock._open_config = MagicMock(spec=())
    plugin_mock._last_version = '0.6.1'
    mocker.patch('plugin.__version__', '0.7.0')
    await plugin_mock.pass_login_credentials('step', 'credentials', [auth_cookie])
    plugin_mock._open_config.assert_called_once_with(OPTIONS_MODE.NEWS)


@pytest.mark.asyncio
async def test_open_welcome_on_authenticate(plugin_mock, auth_cookie):
    plugin_mock._open_config = MagicMock(spec=())
    await plugin_mock.authenticate(stored_credentials=auth_cookie)
    plugin_mock._open_config.assert_called_once_with(OPTIONS_MODE.WELCOME)


@pytest.mark.asyncio
async def test_open_options_on_clicking_install(plugin_mock, delayed_fn):
    plugin_mock._open_config = MagicMock(spec=())
    await asyncio.gather(
        delayed_fn(0.1, plugin_mock.install_game),
        delayed_fn(0.2, plugin_mock.install_game)
    )
    plugin_mock._open_config.assert_called_once()