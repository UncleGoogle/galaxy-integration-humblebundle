import pytest
import json
from unittest.mock import Mock, PropertyMock
from functools import partial
import inspect

from settings import OwnedSettings
from library import LibraryResolver, Strategy
from consts import SOURCE
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
    def fn(plugin_mock, owned_config):
        plugin_mock._library_resolver._settings.update(owned_config)
    return fn


@pytest.fixture
def get_torchlight(orders_keys, get_troves):
    # torchlight has drm-free downloads and steam key; comes also with trove
    for i in orders_keys:
        if i['product']['machine_name'] == 'torchlight_storefront':
            torchlight_order = i
    troves_data = get_troves(from_index=0)
    for i in troves_data:
        if i['machine_name'] == 'torchlight_trove':
            trove_torchlight = i
    return torchlight_order, trove_torchlight


@pytest.mark.asyncio
async def test_library_cache(plugin_mock, get_torchlight, change_settings, orders_keys):
    torchlight, trove_torchlight = get_torchlight

    drm_free = Subproduct(torchlight['subproducts'][0])
    trove = TroveGame(trove_torchlight)
    key = Key(torchlight['tpkd_dict']['all_tpks'][0])

    plugin_mock.push_cache.reset_mock()  # reset initial settings push
    change_settings(plugin_mock, {'library': ['drm-free'], 'show_revealed_keys': True})
    result = await plugin_mock._library_resolver(Strategy.FETCH)
    assert result[drm_free.machine_name] == drm_free
    # cache and calls to api
    assert torchlight in json.loads(plugin_mock.persistent_cache['library'])['orders']
    assert plugin_mock.push_cache.call_count == 1
    assert plugin_mock._api.get_gamekeys.call_count == 1
    assert plugin_mock._api.get_order_details.call_count == len(orders_keys)

    plugin_mock._api.get_gamekeys.reset_mock()
    plugin_mock._api.get_order_details.reset_mock()

    change_settings(plugin_mock, {'library': ['trove']})
    result = await plugin_mock._library_resolver(Strategy.FETCH)
    assert result[trove.machine_name] == trove
    assert trove_torchlight in json.loads(plugin_mock.persistent_cache['library'])['troves']
    # cache and calls to api
    assert plugin_mock._api.get_gamekeys.call_count == 0  # only troves are checked
    assert plugin_mock._api.get_order_details.call_count == 0
    assert plugin_mock._api.get_trove_details.call_count == 1  # from chunk no. 0

    change_settings(plugin_mock, {'library': ['keys']})
    result = await plugin_mock._library_resolver(Strategy.FETCH)
    assert result[key.machine_name] == key
    # strategy.FETCH: ignore cache, all again
    assert plugin_mock._api.get_gamekeys.call_count == 1
    assert plugin_mock._api.get_order_details.call_count == len(orders_keys)
    

@pytest.mark.asyncio
async def test_library_cache_orders(plugin_mock, get_torchlight, change_settings, orders_keys):
    torchlight, _ = get_torchlight

    drm_free = Subproduct(torchlight['subproducts'][0])
    key = Key(torchlight['tpkd_dict']['all_tpks'][0])

    change_settings(plugin_mock, {'library': ['drm-free'], 'show_revealed_keys': True})
    result = await plugin_mock._library_resolver(Strategy.FETCH)
    assert result[drm_free.machine_name] == drm_free

    plugin_mock._api.get_gamekeys.reset_mock()
    plugin_mock._api.get_order_details.reset_mock()

    change_settings(plugin_mock, {'library': ['keys']})
    result = await plugin_mock._library_resolver(Strategy.CACHE)
    assert result[key.machine_name] == key
    # remove previous game
    assert drm_free.machine_name not in result
    # strategy.CACHE do not call to api
    assert plugin_mock._api.get_gamekeys.call_count == 0
    assert plugin_mock._api.get_order_details.call_count == 0
    

@pytest.mark.asyncio
async def test_library_mixed_orders(plugin_mock, get_torchlight, change_settings):
    """Refresh reveals keys only if needed"""
    torchlight, _ = get_torchlight
    key = Key(torchlight['tpkd_dict']['all_tpks'][0])
    # strategy.FETCH: pull all info and put in cache
    change_settings(plugin_mock, {'library': ['keys'], 'show_revealed_keys': False})
    result = await plugin_mock._library_resolver(Strategy.FETCH)
    assert result[key.machine_name] == key
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
    # strategy.MIXED should refresh only orders that may change: those with any unrevealed key
    change_settings(plugin_mock, {'library': ['keys'], 'show_revealed_keys': False})
    result = await plugin_mock._library_resolver(Strategy.MIXED)
    assert key.machine_name not in result  # revealed -> removed
    assert plugin_mock._api.get_gamekeys.call_count == 1
    assert plugin_mock._api.get_order_details.call_count == len(unrevealed_order_keys)
    