import pytest
import time
from functools import partial
from unittest.mock import Mock

from galaxy.api.errors import UnknownError

from consts import SOURCE
from settings import LibrarySettings
from library import LibraryResolver, KeyInfo
from model.game import Subproduct, Key, KeyGame


@pytest.fixture
def create_resolver(plugin):
    def fn(settings, cache={}):
        return LibraryResolver(
            api=plugin._api,
            settings=settings,
            cache=cache,
            save_cache_callback=partial(plugin._save_cache, 'library')
        )
    return fn


@pytest.fixture
def change_settings():
    def fn(plugin, lib_config):
        plugin._library_resolver._settings.update(lib_config)
    return fn


@pytest.fixture
def get_torchlight(orders_keys):
    for i in orders_keys:
        if i['product']['machine_name'] == 'torchlight_storefront':
            torchlight_order = i
    drm_free = Subproduct(torchlight_order['subproducts'][0])
    key = Key(torchlight_order['tpkd_dict']['all_tpks'][0])
    key_game = KeyGame(key, key.machine_name, key.human_name)
    return torchlight_order, drm_free, key_game


# ------ library: all info stored in cache ------

@pytest.mark.asyncio
async def test_library_cache_drm_free(create_resolver, get_torchlight):
    order, game, _ = get_torchlight
    sources = {SOURCE.DRM_FREE}
    cache = {'orders': {'mock_order_id': order}}
    library = create_resolver(LibrarySettings(sources), cache)
    assert {game.machine_name: game} == await library(only_cache=True)


@pytest.mark.asyncio
async def test_library_cache_key(create_resolver, get_torchlight):
    order, _, key = get_torchlight
    sources = {SOURCE.KEYS}
    cache = {'orders': {'mock_order_id': order}}
    library = create_resolver(LibrarySettings(sources), cache)
    assert {key.machine_name: key} == await library(only_cache=True)


# ------ library: fetching info from API ---------

@pytest.mark.asyncio
async def test_library_cache_orders(plugin, get_torchlight, change_settings):
    _, drm_free, key_game = get_torchlight

    change_settings(plugin, {'sources': ['drm-free'], 'show_revealed_keys': True})
    result = await plugin._library_resolver()
    assert result[drm_free.machine_name] == drm_free

    plugin._api.get_gamekeys.reset_mock()
    plugin._api.get_order_details.reset_mock()

    change_settings(plugin, {'sources': ['keys']})
    result = await plugin._library_resolver(only_cache=True)
    assert result[key_game.machine_name] == key_game
    assert drm_free.machine_name not in result
    # no api calls if cache used
    assert plugin._api.get_gamekeys.call_count == 0
    assert plugin._api.get_order_details.call_count == 0


@pytest.mark.asyncio
async def test_library_fetch_with_cache_orders(plugin, get_torchlight, change_settings):
    """Refresh reveals keys only if needed"""
    torchlight, _, key = get_torchlight

    change_settings(plugin, {'sources': ['keys'], 'show_revealed_keys': False})
    result = await plugin._library_resolver()

    # reveal all keys in torchlight order
    for i in plugin._api.orders:
        if i == torchlight:
            for tpk in i['tpkd_dict']['all_tpks']:
                tpk['redeemed_key_val'] = 'redeemed mock code'
            break
    # Get orders that has at least one unrevealed key
    unrevealed_order_keys = []
    for i in plugin._api.orders:
        if any(('redeemed_key_val' not in x for x in i['tpkd_dict']['all_tpks'])):
            unrevealed_order_keys.append(i['gamekey'])

    # reset mocks
    plugin._api.get_gamekeys.reset_mock()
    plugin._api.get_order_details.reset_mock()

    # cache "fetch_in" time has not passed:
    # refresh only orders that may change - those with any unrevealed key
    change_settings(plugin, {'sources': ['keys'], 'show_revealed_keys': False})
    result = await plugin._library_resolver()
    assert key.machine_name not in result  # revealed key should not be shown
    assert plugin._api.get_gamekeys.call_count == 1
    assert plugin._api.get_order_details.call_count == len(unrevealed_order_keys)


@pytest.mark.asyncio
async def test_library_cache_period(plugin, change_settings, orders_keys):
    """Refresh reveals keys only if needed"""
    change_settings(plugin, {'sources': ['keys'], 'show_revealed_keys': False})

    # set expired next fetch
    plugin._library_resolver._cache['next_fetch_orders'] = time.time() - 10

    # cache "fetch_in" time has passed: refresh all
    await plugin._library_resolver()
    assert plugin._api.get_gamekeys.call_count == 1
    assert plugin._api.get_order_details.call_count == len(orders_keys)


# --------test fetching orders-------------------

@pytest.mark.asyncio
async def test_fetch_orders_filter_errors_ok(plugin, create_resolver):
    resolver = create_resolver(Mock())
    await resolver._fetch_orders([])

@pytest.mark.asyncio
async def test_fetch_orders_filter_errors_all_bad(plugin, create_resolver):
    resolver = create_resolver(Mock())
    plugin._api.get_gamekeys.return_value = ['this_will_give_UnknownError', 'this_too']
    with pytest.raises(UnknownError):
        await resolver._fetch_orders([])

@pytest.mark.asyncio
async def test_fetch_orders_filter_errors_one_404(plugin, create_resolver, caplog):
    """404 for specific order key"""
    resolver = create_resolver(Mock())
    resolver = create_resolver(Mock())
    real_gamekeys = await plugin._api.get_gamekeys()
    plugin._api.get_gamekeys.return_value = [real_gamekeys[0], 'this_will_give_UnknownError']
    caplog.clear()
    orders = await resolver._fetch_orders([])
    assert len(orders) == 1
    assert 'UnknownError' in caplog.text
    assert caplog.records[0].levelname == 'ERROR'


# --------test splitting keys -------------------

@pytest.mark.parametrize('human_name, category, blacklist, is_multigame', [
    ('Warhammer 40,000: Space Wolf', 'bundle', [], False),  # no ', ' in human_name
    ('Gremlins, Inc.', 'storefront', [], False),  # not bundle category
    ('Gremlins, Inc.', 'bundle', ['Here, there', 'Gremlins, I'], False),  # blacklisted
    ('Gremlins, Inc.', 'bundle', ['Here, there', 'Gremlins, no match'], True),
    ('Alpha Protocol, Company of Heroes, Rome: Total War, Hell Yeah! Wrath of the Dead Rabbit', 'bundle', [], True),
])
def test_is_multigame_key(human_name, category, blacklist, is_multigame):
    """Most common case where 1 key == 1 game"""
    key = Key({
        "machine_name": "mock_machine_name",
        "human_name": human_name,
        "key_type_human_name": "Steam Key"
    })
    assert LibraryResolver._is_multigame_key(key, category, blacklist) == is_multigame


def test_split_multigame_key():
    tpks = {
        "machine_name": "sega",
        "human_name": "Alpha Protocol, Company of Heroes, Rome: Total War, Hell Yeah! Wrath of the Dead Rabbit",
    }
    key = Key(tpks)
    assert LibraryResolver._split_multigame_key(key) == [
        KeyGame(key, "sega_0", "Alpha Protocol"),
        KeyGame(key, "sega_1", "Company of Heroes"),
        KeyGame(key, "sega_2", "Rome: Total War"),
        KeyGame(key, "sega_3", "Hell Yeah! Wrath of the Dead Rabbit")
    ]


def test_get_key_info():
    key_data_1 = {
        "machine_name": "g1",
        "human_name": 'G1'
    }
    key_data_2 = {
        "machine_name": "g2",
        "human_name": 'G2'
    }
    key_data_3 = {
        "machine_name": "g3",
        "human_name": 'G3'
    }
    orders = [
        {
            'product': {
                'category': 'bundle'
            },
            'tpkd_dict': {
                'all_tpks': [
                    key_data_1,
                    key_data_2
                ]
            }
        },
        {
            'product': {
                'category': 'storefront'
            },
            'tpkd_dict': {
                'all_tpks': [
                    key_data_3
                ]
            }
        },
    ]
    assert LibraryResolver._get_key_infos(orders) == [
        KeyInfo(Key(key_data_1), 'bundle'),
        KeyInfo(Key(key_data_2), 'bundle'),
        KeyInfo(Key(key_data_3), 'storefront'),
    ]
