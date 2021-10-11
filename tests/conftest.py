import pytest
import asyncio
import pathlib
import json
from unittest.mock import MagicMock, Mock

# workaround for vscode test discovery
import sys
sys.path.insert(0, str(pathlib.PurePath(__file__).parent.parent / 'src'))

from galaxy.api.errors import UnknownError
from plugin import HumbleBundlePlugin
from settings import Settings


class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)


async def aiter(seq):
    """Helper for mocking asynchonous generators"""
    for item in seq:
        yield item


@pytest.fixture
def delayed_fn():
    async def fn(delay, awaitable, *args, **kwargs):
        await asyncio.sleep(delay)
        await awaitable(*args, **kwargs)
    return fn


@pytest.fixture
def settings(mocker):
    mocker.patch('plugin.Settings._load_config_file')
    mock = Settings()
    mock.save_config = Mock()
    return mock


@pytest.fixture
def api_mock_raw():
    mock = MagicMock(spec=())
    mock.authenticate = AsyncMock()
    mock.get_order_details = AsyncMock()
    mock.get_gamekeys = AsyncMock()
    mock.get_montly_trove_data = AsyncMock()
    mock.get_subscription_plan = AsyncMock()
    mock.get_trove_details = AsyncMock()
    mock.sign_url_trove = AsyncMock()
    mock.sign_url_subproduct = AsyncMock()
    mock.close_session = AsyncMock()
    mock.get_choice_content_data = AsyncMock()
    mock.get_subscriber_hub_data = AsyncMock()
    mock.get_choice_month_details = AsyncMock(return_value=MagicMock())
    mock.get_choice_marketing_data = AsyncMock(return_value=MagicMock())
    mock.get_subscription_products_with_gamekeys = AsyncMock(return_value=MagicMock())

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
        raise UnknownError()

    mock.TROVES_PER_CHUNK = 20
    mock.get_gamekeys.return_value = [i['gamekey'] for i in mock.orders]
    mock.get_order_details.side_effect = get_details
    mock.get_trove_details.side_effect = lambda from_chunk: get_troves(from_chunk)

    return mock


@pytest.fixture
async def plugin(api_mock, settings, mocker):
    mocker.patch('plugin.AuthorizedHumbleAPI', return_value=api_mock)
    mocker.patch('settings.Settings', return_value=settings)
    plugin = HumbleBundlePlugin(Mock(), Mock(), "handshake_token")
    plugin.push_cache = Mock(spec=())

    plugin._installed_check.cancel()
    plugin._statuses_check.cancel()
    plugin.handshake_complete()

    yield plugin
    await plugin.shutdown()


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
