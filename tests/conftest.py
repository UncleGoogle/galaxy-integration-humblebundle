import pytest
import pathlib
import json
import asyncio
from unittest.mock import MagicMock, patch

# workaround for vscode test discovery
# disable in production!
import sys
sys.path.insert(0, str(pathlib.PurePath(__file__).parent.parent / 'src'))
sys.path.insert(0, str(pathlib.PurePath(__file__).parent.parent / 'galaxy-integrations-python-api' / 'src'))

from galaxy.api.errors import UnknownError
from plugin import HumbleBundlePlugin
from webservice import AuthorizedHumbleAPI
from library import LibraryResolver


class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)


@pytest.fixture
def api_mock_raw():
    mock = MagicMock(spec=())
    mock.authenticate = AsyncMock()
    mock.get_order_details = AsyncMock()
    mock.get_gamekeys = AsyncMock()
    mock.had_trove_subscription = AsyncMock()
    mock.get_trove_sign_url = AsyncMock()
    mock.get_trove_details = AsyncMock()
    mock.close_session = AsyncMock()
    return mock


@pytest.fixture
def api_mock(api_mock_raw, orders_keys, get_troves):
    mock = api_mock_raw
    mock.orders = orders_keys

    def get_details(gamekey):
        for i in mock.orders:
            if i['gamekey'] == gamekey:
                return i
        print('got 404 for gamekey: ' + gamekey)
        raise UnknownError

    mock.TROVES_PER_CHUNK = 20
    mock.get_gamekeys.return_value = [i['gamekey'] for i in mock.orders]
    mock.get_order_details.side_effect = get_details
    mock.had_trove_subscription.return_value = True
    mock.get_trove_details.side_effect = lambda from_chunk: get_troves(from_chunk)

    return mock


@pytest.fixture
async def plugin_mock(api_mock, mocker):
    mocker.patch('plugin.AuthorizedHumbleAPI', return_value=api_mock)
    plugin = HumbleBundlePlugin(MagicMock(), MagicMock(), "handshake_token")
    plugin.push_cache = MagicMock(spec=())

    plugin._check_installed_task.cancel()
    plugin._check_statuses_task.cancel()
    plugin.handshake_complete()

    yield plugin
    plugin.shutdown()


@pytest.fixture
def get_data():
    def fn(source):
        path = pathlib.Path(__file__).parent / 'data' / source
        with open(path, 'r') as f:
            return json.load(f)
    return fn


@pytest.fixture
def orders(get_data):
    return get_data('orders.json')


@pytest.fixture
def orders_keys(get_data):
    return get_data('orders_keys.json')


@pytest.fixture
def origin_bundle_order(get_data):
    return get_data('origin_bundle_order.json')


@pytest.fixture
def overgrowth(get_data):
    return get_data('overgrowth.json')


@pytest.fixture
def get_troves(get_data):
    def fn(from_index=0):
        troves = []
        for i in range(from_index, 4):
            troves.extend(get_data(f'troves_{i + 1}.json'))
        return troves
    return fn