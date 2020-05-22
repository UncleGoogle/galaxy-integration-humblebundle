from unittest.mock import MagicMock, Mock
import pytest

from galaxy.api.types import SubscriptionGame, Subscription
from conftest import aiter

from model.game import TroveGame
from model.subscription import ChoiceMonth


@pytest.fixture
def plugin_with_sub(plugin):
    """
    plugin._subscription_months internal cache is expected to be set at time of getting subscriptions
    """
    plugin._subscription_months = [
        ChoiceMonth({
            "machine_name": "may_2020_choice",
            "short_human_name": "May 2020",
            "monthly_product_page_url": "/subscription/may-2020"
        }, is_active=True),
        ChoiceMonth({
            "machine_name": "april_2020_choice",
            "short_human_name": "April 2020",
            "monthly_product_page_url": "/subscription/april-2020",
            "item_count": 12
        }, is_active=False),
        ChoiceMonth({
            "machine_name": "march_2020_choice",
            "short_human_name": "March 2020",
            "monthly_product_page_url": "/subscription/march-2020",
            "item_count": 12
        }, is_active=False)
    ]
    return plugin


@pytest.mark.asyncio
async def test_get_subscriptions_never_subscribed(api_mock, plugin_with_sub):
    api_mock.had_subscription.return_value = False

    res = await plugin_with_sub.get_subscriptions()
    assert res == [
        Subscription("Humble Choice 2020-05", owned=False),
        Subscription("Humble Trove", owned=False),
    ]


@pytest.mark.asyncio
async def test_get_subscriptions_subscriber_all_from_api(api_mock, plugin_with_sub):
    api_mock.had_subscription.return_value = True
    content_choice_options = [
        Mock(**{'product_machine_name': 'may_2020_choice', 'is_active_content': True}),
        Mock(**{'product_machine_name': 'april_2020_choice', 'is_active_content': False}),
        Mock(**{'product_machine_name': 'march_2020_choice', 'is_active_content': False}),
        Mock(**{'product_machine_name': 'february_2020_choice', 'is_active_content': False}),
        Mock(**{'product_machine_name': 'january_2020_choice', 'is_active_content': False}),
        Mock(**{'product_machine_name': 'december_2019_choice', 'is_active_content': False}),
    ]
    api_mock.get_subscription_products_with_gamekeys = MagicMock(return_value=aiter(content_choice_options))

    res = await plugin_with_sub.get_subscriptions()
    assert sorted(res, key=lambda x: x.subscription_name) == [
        Subscription("Humble Choice 2019-12", owned=True),
        Subscription("Humble Choice 2020-01", owned=True),
        Subscription("Humble Choice 2020-02", owned=True),
        Subscription("Humble Choice 2020-03", owned=True),
        Subscription("Humble Choice 2020-04", owned=True),
        Subscription("Humble Choice 2020-05", owned=True),
        Subscription("Humble Trove", owned=True),
    ]


@pytest.mark.asyncio
async def test_get_subscriptions_current_month_not_unlocked_yet(api_mock, plugin_with_sub):
    api_mock.had_subscription.return_value = True
    subscription_plan = {
        "human_name": "Month-to-Month Classic Plan",
        "length": 1,
        "machine_name": "monthly_basic",
        "pricing|money": {
            "currency": "USD",
            "amount": 12
        }
    }
    api_mock.get_choice_content_data.return_value = Mock(**{'user_subscription_plan': subscription_plan})
    content_choice_options = [
        Mock(**{'product_machine_name': 'april_2020_choice', 'is_active_content': False}),
    ]
    api_mock.get_subscription_products_with_gamekeys = MagicMock(return_value=aiter(content_choice_options))

    res = await plugin_with_sub.get_subscriptions()
    assert sorted(res, key=lambda x: x.subscription_name) == [
        Subscription("Humble Choice 2020-05", owned=True),  # as it is going to be unlocked
        Subscription("Humble Choice 2020-04", owned=True),
        Subscription("Humble Trove", owned=True),
    ]


# @pytest.mark.asyncio
# async def test_get_subscriptions_past_subscriber(api_mock, plugin_with_sub):
#     """
#     Testcase: Currently no subscribtion but was subscriber in the past
#     Excpected: Active subscription months + Trove & currently active month as not owned
#     """
#     api_mock.had_subscription.return_value = True
#     content_choice_options = [
#         Mock(**{'product_machine_name': 'march_2020_choice', 'is_active_content': False}),
#         Mock(**{'product_machine_name': 'february_2020_choice', 'is_active_content': False}),
#     ]
#     api_mock.get_subscription_products_with_gamekeys = MagicMock(return_value=aiter(content_choice_options))
    # res = await plugin_with_sub.get_subscriptions()
    # assert sorted(res, key=lambda x: x.subscription_name) == [
#         Subscription("Humble Choice 2020-05", owned=False),
#         Subscription("Humble Choice 2020-03", owned=True),
#         Subscription("Humble Choice 2020-02", owned=True),
#         Subscription("Humble Trove", owned=False),
#     ]


@pytest.mark.asyncio
async def test_get_subscription_games_trove(api_mock, plugin):
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
async def test_subscription_games_cache_trove(api_mock, plugin):
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
