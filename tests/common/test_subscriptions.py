from unittest.mock import MagicMock, Mock
import pytest

from galaxy.api.types import Subscription
from conftest import aiter

from model.subscription import ChoiceMonth
from model.types import Tier


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
async def test_get_subscriptions_multiple_where_one_paused(api_mock, plugin_with_sub):
    api_mock.had_subscription.return_value = True
    content_choice_options = [
        {'contentChoiceData': Mock(dict), 'gamekey': Mock(str), 'productMachineName': 'may_2020_choice', 'isActiveContent': True},
        {'contentChoiceData': Mock(dict), 'gamekey': Mock(str), 'productMachineName': 'april_2020_choice', 'isActiveContent': False},
        {'contentChoiceData': Mock(dict), 'productMachineName': 'march_2020_choice', 'isActiveContent': False},  # paused month
        {'contentChoiceData': Mock(dict), 'gamekey': Mock(str), 'productMachineName': 'february_2020_choice', 'isActiveContent': False},
        {'contentChoiceData': Mock(dict), 'gamekey': Mock(str), 'productMachineName': 'january_2020_choice', 'isActiveContent': False},
        {'contentChoiceData': Mock(dict), 'gamekey': Mock(str), 'productMachineName': 'december_2019_choice', 'isActiveContent': False},
    ]
    api_mock.get_subscription_products_with_gamekeys = MagicMock(return_value=aiter(content_choice_options))

    res = await plugin_with_sub.get_subscriptions()
    assert sorted(res, key=lambda x: x.subscription_name) == [
        Subscription("Humble Choice 2019-12", owned=True),
        Subscription("Humble Choice 2020-01", owned=True),
        Subscription("Humble Choice 2020-02", owned=True),
        Subscription("Humble Choice 2020-03", owned=False),  # paused month
        Subscription("Humble Choice 2020-04", owned=True),
        Subscription("Humble Choice 2020-05", owned=True),
        Subscription("Humble Trove", owned=True),
    ]


@pytest.mark.asyncio
async def test_get_subscriptions_humble_choice_and_humble_monthly(api_mock, plugin_with_sub):
    """
    The subscription_products_with_gamekeys API returns firstly Choice months data, then old Humble Monthly subscription data.
    Expected: Plugin should ignore Humble Montly subscription months.
    """
    api_mock.had_subscription.return_value = True
    content_choice_options = [
        {'contentChoiceData': Mock(dict), 'gamekey': Mock(str), 'productMachineName': 'january_2020_choice', 'isActiveContent': True},
        {'contentChoiceData': Mock(dict), 'gamekey': Mock(str), 'productMachineName': 'december_2019_choice', 'isActiveContent': False},
        {'machine_name': 'december_2019_monthly', 'order_url': '/downloads?key=b6BVmZ4AuvPwfa3S', 'short_human_name': 'December 2019'},  # subscribed
        {'machine_name': 'november_2019_monthly', 'order_url': None, 'short_human_name': 'November 2019'},  # not subscribed
    ]
    api_mock.get_subscription_products_with_gamekeys = MagicMock(return_value=aiter(content_choice_options))

    res = await plugin_with_sub.get_subscriptions()
    assert sorted(res, key=lambda x: x.subscription_name) == [
        Subscription("Humble Choice 2019-12", owned=True),
        Subscription("Humble Choice 2020-01", owned=True),
        Subscription("Humble Trove", owned=True),
    ]


@pytest.mark.asyncio
async def test_get_subscriptions_past_subscriber(api_mock, plugin_with_sub):
    """
    Testcase: Currently no subscriptiion but user was subscriber in the past
    Expected: Active subscription months + not owned Trove & and owned active month
    """
    api_mock.had_subscription.return_value = True
    api_mock.get_choice_content_data.return_value = Mock(**{'user_subscription_plan': None})
    content_choice_options = [
        {'contentChoiceData': Mock(dict), 'gamekey': Mock(str), 'productMachineName': 'march_2020_choice', 'isActiveContent': False},
        {'contentChoiceData': Mock(dict), 'gamekey': Mock(str), 'productMachineName': 'february_2020_choice', 'isActiveContent': False},
    ]
    api_mock.get_subscription_products_with_gamekeys = MagicMock(return_value=aiter(content_choice_options))

    res = await plugin_with_sub.get_subscriptions()
    assert sorted(res, key=lambda x: x.subscription_name) == [
        Subscription("Humble Choice 2020-02", owned=True),
        Subscription("Humble Choice 2020-03", owned=True),
        Subscription("Humble Choice 2020-05", owned=False),
        Subscription("Humble Trove", owned=False),
    ]


@pytest.mark.parametrize('current_subscription_plan,current_month_owned,trove_owned', [
    pytest.param(None, False, False, id='No subscription'),
    pytest.param(Mock(tier=Tier.LITE), False, True, id='Lite'),
    pytest.param(Mock(tier=Tier.BASIC), True, True, id='Basic'),
    pytest.param(Mock(tier=Tier.PREMIUM), True, True, id='Premium'),
    pytest.param(Mock(tier=Tier.CLASSIC), True, True, id='Classic')
])
@pytest.mark.asyncio
async def test_get_subscriptions_current_month_not_unlocked_yet(
        current_subscription_plan, current_month_owned, trove_owned,
        api_mock, plugin_with_sub
    ):
    """
    Technically only unlocked choice months are owned (locked are not already payed and can be canceled).
    But for user convenience plugin marks month as owned if it *is going to* be unloacked (if not cancelled untill last Friday).
    Without this, Galaxy won't display games until user manualy select current month as owned.
    This would be annoying, as a new subscription month happen... well every month.
    ---
    Test checks also logic for Trove ownership base on subscription status.
    """
    api_mock.had_subscription.return_value = True
    api_mock.get_choice_content_data.return_value = Mock(user_subscription_plan=current_subscription_plan)
    content_choice_options = [
        {'contentChoiceData': Mock(dict), 'gamekey': Mock(str), 'productMachineName': 'april_2020_choice', 'isActiveContent': False}
    ]
    api_mock.get_subscription_products_with_gamekeys = MagicMock(return_value=aiter(content_choice_options))
    res = await plugin_with_sub.get_subscriptions()
    assert sorted(res, key=lambda x: x.subscription_name) == [
        Subscription("Humble Choice 2020-04", owned=True),  # came from api - we're sure that choice month was unlocked
        Subscription("Humble Choice 2020-05", owned=current_month_owned),
        Subscription("Humble Trove", owned=trove_owned),
    ]

