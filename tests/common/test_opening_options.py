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


@pytest.mark.asyncio
@pytest.mark.parametrize('had_sub', [True, False])
@pytest.mark.parametrize('curr_ver, last_ver, proper_versions', [
    ('0.9.4', '0.9.3', True),
    ('0.9.4', '0.9.0', True),
    ('0.9.4', '0.9.4', False),
    ('0.9.5', '0.9.4', False),
    ('0.10.5', '0.10.1', False),
])
async def test_open_news_on_0_9_4_version(
    had_sub, curr_ver, last_ver, proper_versions,
    api_mock, plugin, auth_cookie, mocker
):
    plugin._open_config = MagicMock(spec=())
    api_mock.had_subscription.return_value = had_sub
    plugin._last_version = last_ver
    mocker.patch('plugin.__version__', curr_ver)
    await plugin.authenticate(stored_credentials=auth_cookie)
    if proper_versions and had_sub:
        plugin._open_config.assert_called_once_with(OPTIONS_MODE.NEWS)
        api_mock.had_subscription.assert_called_once()
    else:
        plugin._open_config.assert_not_called()
