from unittest.mock import MagicMock, Mock
import pytest

from galaxy.api.types import Subscription
from conftest import aiter

from model.subscription import UserSubscriptionInfo, UserSubscriptionPlan
from model.types import Tier


@pytest.fixture
def subscriber_info(api_mock):
    mock = Mock(UserSubscriptionInfo, user_plan=Mock(UserSubscriptionPlan))
    api_mock.get_subscriber_info_optional.return_value = mock
    return mock


@pytest.fixture
def api_at_may_2020(api_mock, subscriber_info):
    active_product_name = "may_2020_choice"
    api_mock.get_choice_marketing_data.return_value = {
        "activeContentMachineName": active_product_name
    }
    subscriber_info.active_content_product_machine_name=active_product_name
    return api_mock


@pytest.mark.asyncio
async def test_get_subscriptions_never_subscribed(plugin, api_at_may_2020):
    api_at_may_2020.get_subscriber_info_optional.return_value = None
    api_at_may_2020.get_subscription_products_with_gamekeys = MagicMock(return_value=aiter([]))

    res = await plugin.get_subscriptions()
    assert sorted(res, key=lambda x: x.subscription_name) == [
        Subscription("Humble Choice 2020-05", owned=False),
        Subscription("Humble Trove", owned=False),
    ]


@pytest.mark.asyncio
async def test_get_subscriptions_multiple_where_one_paused(plugin, api_at_may_2020, subscriber_info):
    subscriber_info.subscription_expired.return_value = False
    content_choice_options = [
        {'contentChoiceData': Mock(dict), 'gamekey': Mock(str), 'productMachineName': 'may_2020_choice', 'isActiveContent': True},
        {'contentChoiceData': Mock(dict), 'gamekey': Mock(str), 'productMachineName': 'april_2020_choice', 'isActiveContent': False},
        {'contentChoiceData': Mock(dict), 'productMachineName': 'march_2020_choice', 'isActiveContent': False},  # paused month
        {'contentChoiceData': Mock(dict), 'gamekey': Mock(str), 'productMachineName': 'february_2020_choice', 'isActiveContent': False},
    ]
    api_at_may_2020.get_subscription_products_with_gamekeys = MagicMock(return_value=aiter(content_choice_options))

    res = await plugin.get_subscriptions()
    assert sorted(res, key=lambda x: x.subscription_name) == [
        Subscription("Humble Choice 2020-02", owned=True),
        Subscription("Humble Choice 2020-03", owned=False),  # paused month
        Subscription("Humble Choice 2020-04", owned=True),
        Subscription("Humble Choice 2020-05", owned=True),
        Subscription("Humble Trove", owned=True),
    ]


@pytest.mark.asyncio
async def test_get_subscriptions_humble_choice_and_humble_monthly(api_at_may_2020, plugin, subscriber_info):
    """
    The subscription_products_with_gamekeys API returns firstly Choice months data, then old Humble Monthly subscription data.
    Expected: Plugin should ignore Humble Montly subscription months.
    """
    subscriber_info.subscription_expired.return_value = False
    content_choice_options = [
        {'contentChoiceData': Mock(dict), 'gamekey': Mock(str), 'productMachineName': 'january_2020_choice', 'isActiveContent': True},
        {'contentChoiceData': Mock(dict), 'gamekey': Mock(str), 'productMachineName': 'december_2019_choice', 'isActiveContent': False},
        {'machine_name': 'december_2019_monthly', 'order_url': '/downloads?key=b6BVmZ4AuvPwfa3S', 'short_human_name': 'December 2019'},  # subscribed
        {'machine_name': 'november_2019_monthly', 'order_url': None, 'short_human_name': 'November 2019'},  # not subscribed
    ]
    api_at_may_2020.get_subscription_products_with_gamekeys = MagicMock(return_value=aiter(content_choice_options))

    res = await plugin.get_subscriptions()
    assert sorted(res, key=lambda x: x.subscription_name) == [
        Subscription("Humble Choice 2019-12", owned=True),
        Subscription("Humble Choice 2020-01", owned=True),
        Subscription("Humble Trove", owned=True),
    ]


@pytest.mark.asyncio
async def test_get_subscriptions_past_subscriber(api_at_may_2020, plugin, subscriber_info):
    """
    Testcase: Currently no subscription but user was subscriber in the past
    """
    subscriber_info.subscription_expired.return_value = True
    content_choice_options = [
        {'contentChoiceData': Mock(dict), 'gamekey': Mock(str), 'productMachineName': 'march_2020_choice', 'isActiveContent': False},
        {'contentChoiceData': Mock(dict), 'gamekey': Mock(str), 'productMachineName': 'february_2020_choice', 'isActiveContent': False},
    ]
    api_at_may_2020.get_subscription_products_with_gamekeys = MagicMock(return_value=aiter(content_choice_options))

    res = await plugin.get_subscriptions()
    assert sorted(res, key=lambda x: x.subscription_name) == [
        Subscription("Humble Choice 2020-02", owned=True),
        Subscription("Humble Choice 2020-03", owned=True),
        Subscription("Humble Choice 2020-05", owned=False),  # active month
        Subscription("Humble Trove", owned=False),
    ]


@pytest.mark.parametrize('current_subscription_plan,current_month_owned,trove_owned', [
    pytest.param(Mock(tier=Tier.LITE), False, True, id='Lite'),
    pytest.param(Mock(tier=Tier.BASIC), True, True, id='Basic'),
    pytest.param(Mock(tier=Tier.PREMIUM), True, True, id='Premium'),
    pytest.param(Mock(tier=Tier.CLASSIC), True, True, id='Classic')
])
@pytest.mark.asyncio
async def test_get_subscriptions_current_month_not_unlocked_yet(
        current_subscription_plan, current_month_owned, trove_owned,
        api_at_may_2020, plugin, subscriber_info
    ):
    """
    Technically only unlocked choice months are owned (locked are not already payed and can be canceled).
    But for user convenience plugin marks month as owned if it *is going to* be unloacked (if not cancelled untill last Friday).
    Without this, Galaxy won't display games until user manualy select current month as owned.
    This would be annoying, as a new subscription month happen... well every month.
    ---
    Test checks also logic for Trove ownership base on subscription status.
    """
    subscriber_info.user_plan = current_subscription_plan
    subscriber_info.subscription_expired.return_value = False
    content_choice_options = [
        {'contentChoiceData': Mock(dict), 'gamekey': Mock(str), 'productMachineName': 'april_2020_choice', 'isActiveContent': False}
    ]
    api_at_may_2020.get_subscription_products_with_gamekeys = MagicMock(return_value=aiter(content_choice_options))
    res = await plugin.get_subscriptions()
    assert sorted(res, key=lambda x: x.subscription_name) == [
        Subscription("Humble Choice 2020-04", owned=True),  # came from api - we're sure that choice month was unlocked
        Subscription("Humble Choice 2020-05", owned=current_month_owned),
        Subscription("Humble Trove", owned=trove_owned),
    ]

