import pytest
import time
import json
from functools import partial
from unittest.mock import Mock

from galaxy.api.errors import UnknownError

from library import LibraryResolver
from model.game import Subproduct, Key, TroveGame


@pytest.fixture
def create_resolver(plugin_mock):
    def fn(settings, cache={}):
        return LibraryResolver(
            api=plugin_mock._api,
            settings=settings,
            cache=cache,
            save_cache_callback=partial(plugin_mock._save_cache, 'library')
        )
    return fn


@pytest.fixture
def change_settings():
    def fn(plugin_mock, lib_config):
        plugin_mock._library_resolver._settings.update(lib_config)
    return fn


@pytest.fixture
def get_torchlight_trove(get_troves):
    troves_data = get_troves(from_index=0)
    for i in troves_data:
        if i['machine_name'] == 'torchlight_trove':
            trove_torchlight = i
    return trove_torchlight, TroveGame(trove_torchlight)


@pytest.fixture
def get_torchlight(orders_keys):
    for i in orders_keys:
        if i['product']['machine_name'] == 'torchlight_storefront':
            torchlight_order = i
    drm_free = Subproduct(torchlight_order['subproducts'][0])
    key = Key(torchlight_order['tpkd_dict']['all_tpks'][0])
    return torchlight_order, drm_free, key


@pytest.mark.asyncio
async def test_library_trove(plugin_mock, get_torchlight_trove, change_settings):
    trove_torch_data, trove = get_torchlight_trove

    change_settings(plugin_mock, {'sources': ['trove']})
    result = await plugin_mock._library_resolver()
    assert result[trove.machine_name] == trove
    assert trove_torch_data in json.loads(plugin_mock.persistent_cache['library'])['troves']

    # cache and calls to api
    assert plugin_mock._api.get_gamekeys.call_count == 0  # only troves are checked
    assert plugin_mock._api.get_order_details.call_count == 0
    assert plugin_mock._api.get_trove_details.call_count == 1  # from chunk no. 0


@pytest.mark.asyncio
async def test_library_cache_orders(plugin_mock, get_torchlight, change_settings):
    _, drm_free, key = get_torchlight

    change_settings(plugin_mock, {'sources': ['drm-free'], 'show_revealed_keys': True})
    result = await plugin_mock._library_resolver()
    assert result[drm_free.machine_name] == drm_free

    plugin_mock._api.get_gamekeys.reset_mock()
    plugin_mock._api.get_order_details.reset_mock()

    change_settings(plugin_mock, {'sources': ['keys']})
    result = await plugin_mock._library_resolver(only_cache=True)
    assert result[key.machine_name] == key.key_games[0]
    assert drm_free.machine_name not in result
    # no api calls if cache used
    assert plugin_mock._api.get_gamekeys.call_count == 0
    assert plugin_mock._api.get_order_details.call_count == 0
    

@pytest.mark.asyncio
async def test_library_fetch_with_cache_orders(plugin_mock, get_torchlight, change_settings):
    """Refresh reveals keys only if needed"""
    torchlight, _, key = get_torchlight

    change_settings(plugin_mock, {'sources': ['keys'], 'show_revealed_keys': False})
    result = await plugin_mock._library_resolver()

    # reveal all keys in torchlight order
    for i in plugin_mock._api.orders:
        if i == torchlight:
            for tpk in i['tpkd_dict']['all_tpks']:
                tpk['redeemed_key_val'] = 'redeemed mock code'
            break
    # Get orders that has at least one unrevealed key
    unrevealed_order_keys = []
    for i in plugin_mock._api.orders:
        if any(('redeemed_key_val' not in x for x in i['tpkd_dict']['all_tpks'])):
            unrevealed_order_keys.append(i['gamekey'])

    # reset mocks
    plugin_mock._api.get_gamekeys.reset_mock()
    plugin_mock._api.get_order_details.reset_mock()

    # cache "fetch_in" time has not passed:
    # refresh only orders that may change - those with any unrevealed key
    change_settings(plugin_mock, {'sources': ['keys'], 'show_revealed_keys': False})
    result = await plugin_mock._library_resolver()
    assert key.machine_name not in result  # revealed -> removed
    assert plugin_mock._api.get_gamekeys.call_count == 1
    assert plugin_mock._api.get_order_details.call_count == len(unrevealed_order_keys)
    

@pytest.mark.asyncio
async def test_library_cache_period(plugin_mock, change_settings, orders_keys):
    """Refresh reveals keys only if needed"""
    change_settings(plugin_mock, {'sources': ['keys', 'trove'], 'show_revealed_keys': False})

    # set expired next fetch 
    plugin_mock._library_resolver._cache['next_fetch_orders'] = time.time() - 10
    plugin_mock._library_resolver._cache['next_fetch_troves'] = time.time() - 10

    # cache "fetch_in" time has passed: refresh all
    await plugin_mock._library_resolver()
    assert plugin_mock._api.get_gamekeys.call_count == 1
    assert plugin_mock._api.get_trove_details.call_count == 1
    assert plugin_mock._api.get_order_details.call_count == len(orders_keys)
    assert plugin_mock._api.had_trove_subscription.call_count == 1


# --------test fetching orders-------------------

@pytest.mark.asyncio
async def test_fetch_orders_filter_errors_ok(plugin_mock, create_resolver):
    resolver = create_resolver(Mock())
    await resolver._fetch_orders([])

@pytest.mark.asyncio
async def test_fetch_orders_filter_errors_all_bad(plugin_mock, create_resolver):
    resolver = create_resolver(Mock())
    plugin_mock._api.get_gamekeys.return_value = ['this_will_give_UnknownError', 'this_too']
    with pytest.raises(UnknownError):
        await resolver._fetch_orders([])

@pytest.mark.asyncio
async def test_fetch_orders_filter_errors_one_404(plugin_mock, create_resolver, caplog):
    """404 for specific order key"""
    resolver = create_resolver(Mock())
    resolver = create_resolver(Mock())
    real_gamekeys = await plugin_mock._api.get_gamekeys()
    plugin_mock._api.get_gamekeys.return_value = [real_gamekeys[0], 'this_will_give_UnknownError']
    caplog.clear()
    orders = await resolver._fetch_orders([])
    assert len(orders) == 1
    assert 'UnknownError' in caplog.text
    assert caplog.records[0].levelname == 'ERROR'
