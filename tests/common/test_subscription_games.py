from unittest.mock import MagicMock
import pytest

from conftest import aiter

from galaxy.api.types import SubscriptionGame
from model.game import TroveGame


@pytest.mark.asyncio
async def test_trove(api_mock, plugin):
    parsed_from_page = {
        'newlyAdded': [
            {'human-name': 'A', 'machine_name': 'a'},
            {'human-name': 'Z', 'machine_name': 'z'},
        ]
    }
    api_mock.get_montly_trove_data.return_value = parsed_from_page
    chunks_from_api = [
        [
            {'human-name': 'A', 'machine_name': 'a'},
            {'human-name': 'B', 'machine_name': 'b'},
        ],
        [
            {'human-name': 'C', 'machine_name': 'c'},
            {'human-name': 'D', 'machine_name': 'd'},
        ],
        [
            {'human-name': 'E', 'machine_name': 'e'},
        ],
    ]
    api_mock.get_trove_details = MagicMock(return_value=aiter(chunks_from_api))
    ctx = None
    trove_games = []
    async for bunch in plugin.get_subscription_games('Humble Trove', ctx):
        trove_games.extend(bunch)
    assert sorted(trove_games, key=lambda x: x.game_id) \
        == sorted([
            SubscriptionGame(game_title='A', game_id='a'),
            SubscriptionGame('B', 'b'),
            SubscriptionGame('C', 'c'),
            SubscriptionGame('D', 'd'),
            SubscriptionGame('E', 'e'),
            SubscriptionGame('Z', 'z'),
            SubscriptionGame('A', 'a')  # don't mind returning 2 times the same item
        ], key=lambda x: x.game_id)


@pytest.mark.asyncio
async def test_trove_cache(api_mock, plugin):
    parsed_from_page = {
        'newlyAdded': [
            {'human-name': 'Z', 'machine_name': 'z'}
        ]
    }
    api_mock.get_montly_trove_data.return_value = parsed_from_page
    chunks_from_api = [
        [
            {'human-name': 'A', 'machine_name': 'a'},
            {'human-name': 'B', 'machine_name': 'b'},
        ],
        [
            {'human-name': 'C', 'machine_name': 'c'},
        ],
    ]
    api_mock.get_trove_details = MagicMock(return_value=aiter(chunks_from_api))
    ctx = None
    async for bunch in plugin.get_subscription_games('Humble Trove', ctx):
        pass
    assert plugin._trove_games == {
        'a': TroveGame({'human-name': 'A', 'machine_name': 'a'}),
        'b': TroveGame({'human-name': 'B', 'machine_name': 'b'}),
        'c': TroveGame({'human-name': 'C', 'machine_name': 'c'}),
        'z': TroveGame({'human-name': 'Z', 'machine_name': 'z'}),
    }

@pytest.mark.asyncio
async def test_trove_serialize_to_presistent_cache(plugin):
    plugin._trove_games = {
        'a': TroveGame({'human-name': 'A', 'machine_name': 'a', 'downloads': {'windows': {}}}),
        'c': TroveGame({'human-name': 'C', 'machine_name': 'c', 'downloads': {'mac': {}}}),
    }
    await plugin.subscription_games_import_complete()
    assert plugin.persistent_cache['trove_games'] == '[' \
        '{"human-name": "A", "machine_name": "a", "downloads": {"windows": {}}}, ' \
        '{"human-name": "C", "machine_name": "c", "downloads": {"mac": {}}}' \
    ']'
    plugin.push_cache.assert_called()


@pytest.mark.asyncio
async def test_trove_load_from_persistent_cache(plugin):
    plugin.persistent_cache['trove_games'] = '[' \
        '{"human-name": "A", "machine_name": "a", "downloads": {"windows": {}}}, ' \
        '{"human-name": "C", "machine_name": "c", "downloads": {"mac": {}}}' \
    ']'
    plugin.handshake_complete()
    assert plugin._trove_games == {
        'a': TroveGame({'human-name': 'A', 'machine_name': 'a', 'downloads': {'windows': {}}}),
        'c': TroveGame({'human-name': 'C', 'machine_name': 'c', 'downloads': {'mac': {}}}),
    }
