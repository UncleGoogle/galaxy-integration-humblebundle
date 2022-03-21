from functools import partial, reduce
from unittest.mock import MagicMock, Mock, PropertyMock

from freezegun import freeze_time
import pytest

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


@pytest.fixture
def an_order(get_torchlight):
    return get_torchlight[0]


@pytest.fixture
def an_order_games(get_torchlight):
    return [get_torchlight[1], get_torchlight[2]]


# ------ all info stored in cache ------

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


@pytest.mark.asyncio
async def test_library_resolver_permanently_caches_const_orders(
    api_mock, bulk_api_orders, create_resolver
):
    """
    Test of legacy optimization feature
    `bulk_api_orders` contains some 'const' orders --
    that won't change anymore from plugin perspective
    that is why resolver should not refresh them.
    Probably to be removed as since fetching with orders bulk API
    there is no point for such optimization
    """
    resolver = create_resolver(MagicMock())
    api_mock.get_orders_bulk_details.return_value = bulk_api_orders
    
    # preparing cache
    await resolver()
    all_called_gamekeys = reduce(lambda x, y: x + y[0][0], api_mock.get_orders_bulk_details.call_args_list, [])
    assert set(all_called_gamekeys) == set(bulk_api_orders.keys())
    
    api_mock.get_gamekeys.reset_mock()
    api_mock.get_orders_bulk_details.reset_mock()

    # after subsequent call
    await resolver()
    all_called_gamekeys = reduce(lambda x, y: x + y[0][0], api_mock.get_orders_bulk_details.call_args_list, [])
    assert set(all_called_gamekeys) < set(bulk_api_orders.keys())


@pytest.mark.asyncio
class TestFetchOrdersViaBulkAPI:
    ORDER_DETAILS_DUMMY1 = MagicMock()
    ORDER_DETAILS_DUMMY2 = MagicMock()
    
    @pytest.fixture(autouse=True)
    def resolver(self, create_resolver):
        resolver = create_resolver(Mock())
        cached_gamekeys = []
        self.fetch = partial(resolver._fetch_orders, cached_gamekeys)

    @pytest.mark.parametrize('orders, expected', [
        pytest.param(
            {'key2': ORDER_DETAILS_DUMMY2, 'key1': ORDER_DETAILS_DUMMY1},
            {'key2': ORDER_DETAILS_DUMMY2, 'key1': ORDER_DETAILS_DUMMY1},
            id='small number'
        ),
        pytest.param(
            {'key2': ORDER_DETAILS_DUMMY2, 'key1': None},
            {'key2': ORDER_DETAILS_DUMMY2},
            id='one unknown'
        ),
    ])
    async def test_fetch_orders(self, api_mock, orders, expected): 
        api_mock.get_gamekeys.return_value = ['key1', 'key2']
        api_mock.get_orders_bulk_details.return_value = orders

        result = await self.fetch()
        assert result == expected

    async def test_fetch_by_multiple_batches(self, api_mock): 
        def fake_bulk_api_reponse(gamekeys):
            return {gk: MagicMock(name=gk) for gk in gamekeys}
        
        mock_gamekeys = [f'key{i}' for i in range(82)]
        api_mock.get_gamekeys.return_value = mock_gamekeys
        api_mock.get_orders_bulk_details.side_effect = fake_bulk_api_reponse

        result = await self.fetch()

        assert len(result) == 82
        assert api_mock.get_gamekeys.call_count == 1
        assert api_mock.get_orders_bulk_details.call_count == 3
    

# --------test splitting keys -------------------

@pytest.mark.parametrize('human_name, category, blacklist, is_multigame', [
    ('Warhammer 40,000: Space Wolf', 'bundle', [], False),  # no ', ' in human_name
    ('Gremlins, Inc.', 'storefront', [], False),  # not bundle category
    ('Gremlins, Inc.', 'bundle', ['Here, there', 'Gremlins, I'], False),  # blacklisted
    ('Gremlins, Inc.', 'bundle', ['Here, there', 'Gremlins, no match'], True),
    ('Alpha Protocol, Company of Heroes, Rome: Total War, Hell Yeah! Wrath of the Dead Rabbit', 'bundle', [], True),
    ('Star Wars™ Battlefront™ II (Classic, 2005)', 'bundle', ['STAR WARS™ Battlefront™ II (Classic, 2005)'], False),
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

@pytest.mark.parametrize('machine_name, human_name, expected', [
    ('deepsilver_bundle_initial_steam', 'Metro 2033, Risen, and Sacred Citadel', ['Metro 2033', 'Risen', 'Sacred Citadel']),
    ('test_bundle_a', 'Some Game, Ori and Blind Forest', ['Some Game', 'Ori and Blind Forest']),
    ('test_bundle_b', 'Some Game 1, and Some Game 2, and One More', ['Some Game 1', 'Some Game 2', 'One More']),
    ('test_bundle_c', 'Game 1, And Yet It Moves', ['Game 1', 'And Yet It Moves']),
    ('test_bundle_d', 'And Yet It Moves, and And Yet It Moves', ['And Yet It Moves', 'And Yet It Moves']),
])
def test_split_multigame_key_and(machine_name, human_name, expected):
    # Many bundle keys add the word 'and' before the last game title
    tpks = {
        "machine_name": machine_name,
        "human_name": human_name,
    }
    key = Key(tpks)
    key_games = LibraryResolver._split_multigame_key(key)
    assert len(key_games) == len(expected)

    for idx in range(0, len(expected)):
        assert key_games[idx] == KeyGame(key, f'{key.machine_name}_{idx}', expected[idx])

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


@pytest.mark.parametrize("chunks, expected", [
        ([], []),
        ([1], [[1]]),
        ([1,2,3,4], [[1,2,3],[4]]),
        ([1,2,3,4,5,6], [[1,2,3], [4,5,6]]),
        ([1,2,3,4,5,6,7,8,9,10,11], [[1,2,3],[4,5,6],[7,8,9],[10,11]])
    ]
)
def test_make_chunks(chunks, expected):
    assert expected == list(LibraryResolver._make_chunks(chunks, size=3))


# ----------integration tests with plugin-------------

@pytest.mark.asyncio
@pytest.mark.parametrize("only_cache", [True, False])
async def test_plugin_with_library_returns_proper_games_depending_on_choosen_settings(
    plugin, api_mock, get_torchlight, change_settings, only_cache,
):
    torchlight_order, drm_free, key_game = get_torchlight
    change_settings(plugin, {'sources': ['drm-free'], 'show_revealed_keys': True})
    api_mock.get_orders_bulk_details.return_value = {torchlight_order['gamekey']: torchlight_order}

    # before
    result = await plugin._library_resolver()
    assert result[drm_free.machine_name] == drm_free

    # after
    change_settings(plugin, {'sources': ['keys']})
    result = await plugin._library_resolver(only_cache=only_cache)
    
    assert result[key_game.machine_name] == key_game
    assert drm_free.machine_name not in result


@pytest.mark.asyncio
async def test_plugin_with_library_orders_cached_uses_cache(
    plugin, api_mock, bulk_api_orders,
):
    api_mock.get_orders_bulk_details.return_value = bulk_api_orders

    # before
    await plugin._library_resolver()

    api_mock.get_gamekeys.reset_mock()
    api_mock.get_orders_bulk_details.reset_mock()

    # after
    await plugin._library_resolver(only_cache=True)
    
    assert api_mock.get_gamekeys.call_count == 0
    assert api_mock.get_orders_bulk_details.call_count == 0


@pytest.mark.asyncio
async def test_plugin_with_library_orders_cached_fetches_again_when_called_with_skip_cache(
    plugin, api_mock, bulk_api_orders,
):
    api_mock.get_orders_bulk_details.return_value = bulk_api_orders

    # before
    await plugin._library_resolver()

    api_mock.get_gamekeys.reset_mock()
    api_mock.get_orders_bulk_details.reset_mock()

    # after
    await plugin._library_resolver(only_cache=False)
    
    assert api_mock.get_gamekeys.call_count == 1
    assert api_mock.get_orders_bulk_details.call_count >= 1


@pytest.mark.asyncio
async def test_plugin_with_library_resovler_when_cache_is_invalidated_after_14_days(
    plugin, api_mock, bulk_api_orders
):
    type(api_mock).is_authenticated = PropertyMock(return_value=True)
    api_mock.get_orders_bulk_details.return_value = bulk_api_orders
    with freeze_time('2020-12-01') as frozen_time:
        result_before = await plugin.get_owned_games()
        api_mock.get_gamekeys.reset_mock()
        api_mock.get_orders_bulk_details.reset_mock()

        frozen_time.move_to('2020-12-15')
        result_after = await plugin.get_owned_games()
    
    assert api_mock.get_gamekeys.call_count == 1
    assert api_mock.get_orders_bulk_details.call_count >= 1
    assert len(result_before) == len(result_after) != 0
