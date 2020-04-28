from unittest.mock import MagicMock
import pytest

from galaxy.api.types import SubscriptionGame


async def aiter(seq):
    for item in seq:
        yield item


@pytest.mark.asyncio
async def test_subscription_games_trove(api_mock, plugin):
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
    async for bunch in plugin.get_subscription_games('Trove', ctx):
        trove_games.extend(bunch)
    assert sorted(trove_games, key=lambda x: x.game_id) \
        == sorted([
            SubscriptionGame('a', 'A'),
            SubscriptionGame('b', 'B'),
            SubscriptionGame('c', 'C'),
            SubscriptionGame('d', 'D'),
            SubscriptionGame('e', 'E'),
            SubscriptionGame('z', 'Z'),
            SubscriptionGame('a', 'A')  # don't mind returning 2 times the same item
        ], key=lambda x: x.game_id)
