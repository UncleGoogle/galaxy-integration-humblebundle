from unittest.mock import MagicMock, Mock
import pytest

from galaxy.api.types import Subscription
from conftest import aiter

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
async def test_get_subscriptions_past_subscriber(api_mock, plugin_with_sub):
    """
    Testcase: Currently no subscribtion but user was subscriber in the past
    Expected: Active subscription months + not owned Trove & and owned active month
    """
    api_mock.had_subscription.return_value = True
    api_mock.get_choice_content_data.return_value = Mock(**{'user_subscription_plan': None})
    content_choice_options = [
        Mock(**{'product_machine_name': 'march_2020_choice', 'is_active_content': False}),
        Mock(**{'product_machine_name': 'february_2020_choice', 'is_active_content': False}),
    ]
    api_mock.get_subscription_products_with_gamekeys = MagicMock(return_value=aiter(content_choice_options))

    res = await plugin_with_sub.get_subscriptions()
    assert sorted(res, key=lambda x: x.subscription_name) == [
        Subscription("Humble Choice 2020-02", owned=True),
        Subscription("Humble Choice 2020-03", owned=True),
        Subscription("Humble Choice 2020-05", owned=False),
        Subscription("Humble Trove", owned=False),
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
        Subscription("Humble Choice 2020-04", owned=True),
        Subscription("Humble Choice 2020-05", owned=True),  # as it is going to be unlocked
        Subscription("Humble Trove", owned=True),
    ]

