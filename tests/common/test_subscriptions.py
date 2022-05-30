from unittest.mock import MagicMock, Mock
import typing as t
import json

from galaxy.api.types import Subscription
from conftest import aiter
import pytest

from webservice import WebpackParseError


pytestmark = pytest.mark.asyncio


def assert_contains(alist: t.List, elements: t.Iterable):
    for i in elements:
        if i in alist:
            break
        assert False, f"{i} not found in {alist}"


@pytest.fixture
def api_mock(api_mock):
    active_product_name = "may_2020_choice"
    api_mock.get_user_subscription_state.return_value = Mock(dict)
    api_mock.get_choice_marketing_data.return_value = {
        "activeContentMachineName": active_product_name
    }
    return api_mock


async def test_get_subscriptions_never_subscribed(plugin, api_mock):
    subscription_state = json.loads("""
    {
      "newestOwnedTier": null,
      "nextBilledPlan": "",
      "consecutiveContentDropCount": 0,
      "canResubscribe": false,
      "currentlySkippingContentHumanName": null,
      "perksStatus": "inactive",
      "billDate": "2021-11-30T18:00:00",
      "monthlyNewestOwnedContentMachineName": null,
      "willReceiveFutureMonths": false,
      "monthlyOwnsActiveContent": false,
      "unpauseDt": "2021-12-07T18:00:00",
      "creditsRemaining": 0,
      "currentlySkippingContentMachineName": null,
      "canBeConvertedFromGiftSubToPayingSub": false,
      "lastSkippedContentMachineName": null,
      "contentEndDateAfterBillDate": "2021-12-07T18:00:00",
      "isPaused": false,
      "monthlyNewestOwnedContentGamekey": null,
      "failedBillingMonths": 0,
      "wasPaused": false,
      "monthlyPurchasedAnyContent": false,
      "monthlyNewestOwnedContentEnd": null,
      "monthlyOwnsAnyContent": false
    }
    """)
    api_mock.get_user_subscription_state.return_value = subscription_state
    api_mock.get_subscription_products_with_gamekeys = MagicMock(return_value=aiter([]))
    api_mock.get_subscriber_hub_data.side_effect = WebpackParseError()

    res = await plugin.get_subscriptions()

    assert_contains(res, [Subscription("Humble Choice 2020-05", owned=False)])
    api_mock.get_choice_marketing_data.assert_called_once()


async def test_get_subscriptions_multiple_where_one_paused(plugin, api_mock):
    subscription_state = json.loads("""
    {
      "currentlySkippingContentHumanName": null,
      "currentlySkippingContentMachineName": null,
      "perksStatus": "active",
      "monthlyNewestOwnedContentMachineName": "may_2020_choice",
      "willReceiveFutureMonths": true,
      "monthlyOwnsActiveContent": true,
      "lastSkippedContentMachineName": "march_2020_choice",
      "isPaused": false,
      "wasPaused": false,
      "monthlyOwnsAnyContent": true
    }
    """)
    content_choice_options = [
        {'contentChoiceData': Mock(dict), 'gamekey': Mock(str), 'productMachineName': 'may_2020_choice', 'isActiveContent': True},
        {'contentChoiceData': Mock(dict), 'productMachineName': 'april_2020_choice', 'isActiveContent': False},  # paused month
        {'contentChoiceData': Mock(dict), 'gamekey': Mock(str), 'productMachineName': 'march_2020_choice', 'isActiveContent': False},
    ]
    api_mock.get_user_subscription_state.return_value = subscription_state
    api_mock.get_subscription_products_with_gamekeys = MagicMock(return_value=aiter(content_choice_options))

    res = await plugin.get_subscriptions()

    assert_contains(res, [
        Subscription("Humble Choice 2020-03", owned=True),
        Subscription("Humble Choice 2020-04", owned=False),  # paused month
        Subscription("Humble Choice 2020-05", owned=True),
    ])


async def test_get_subscriptions_humble_choice_and_humble_monthly(api_mock, plugin):
    """
    The subscription_products_with_gamekeys API returns firstly Choice months data, then old Humble Monthly subscription data.
    Testcase: User owned Humble Monthly then it transformed to Humble Choice
    Expected: Plugin should ignore Humble Montly subscription months.
    """
    subscription_state = json.loads("""
    {
      "currentlySkippingContentHumanName": null,
      "currentlySkippingContentMachineName": null,
      "perksStatus": "active",
      "monthlyNewestOwnedContentMachineName": "january_2020_choice",
      "willReceiveFutureMonths": true,
      "monthlyOwnsActiveContent": true,
      "lastSkippedContentMachineName": null,
      "isPaused": false,
      "wasPaused": false,
      "monthlyOwnsAnyContent": true
    }
    """)
    content_choice_options = [
        {'contentChoiceData': Mock(dict), 'gamekey': Mock(str), 'productMachineName': 'january_2020_choice', 'isActiveContent': True},
        {'contentChoiceData': Mock(dict), 'gamekey': Mock(str), 'productMachineName': 'december_2019_choice', 'isActiveContent': False},
        {'machine_name': 'december_2019_monthly', 'order_url': '/downloads?key=b6BVmZ4AuvPwfa3S', 'short_human_name': 'December 2019'},  # subscribed
        {'machine_name': 'november_2019_monthly', 'order_url': None, 'short_human_name': 'November 2019'},  # not subscribed
    ]
    api_mock.get_user_subscription_state.return_value = subscription_state
    api_mock.get_subscription_products_with_gamekeys = MagicMock(return_value=aiter(content_choice_options))

    res = await plugin.get_subscriptions()

    assert_contains(res, [
        Subscription("Humble Choice 2019-12", owned=True),
        Subscription("Humble Choice 2020-01", owned=True),
    ])


async def test_get_subscriptions_past_subscriber(api_mock, plugin):
    """
    Testcase: Currently no subscription but user was subscriber in the past
    Expected: owned months and additionally not owned active month
    Note: I didn't check how exactly real subscription state json looks like in that case
    """
    subscription_state = json.loads("""
    {
      "canResubscribe": true,
      "perksStatus": "inactive",
      "monthlyNewestOwnedContentMachineName": "january_2020_choice",
      "willReceiveFutureMonths": false,
      "monthlyOwnsActiveContent": false,
      "monthlyOwnsAnyContent": true
    }
    """)
    content_choice_options = [
        {'contentChoiceData': Mock(dict), 'gamekey': Mock(str), 'productMachineName': 'march_2020_choice', 'isActiveContent': False},
        {'contentChoiceData': Mock(dict), 'gamekey': Mock(str), 'productMachineName': 'february_2020_choice', 'isActiveContent': False},
    ]
    api_mock.get_user_subscription_state.return_value = subscription_state
    api_mock.get_subscription_products_with_gamekeys = MagicMock(return_value=aiter(content_choice_options))
    api_mock.get_subscriber_hub_data.side_effect = WebpackParseError()

    res = await plugin.get_subscriptions()

    assert_contains(res, [
        Subscription("Humble Choice 2020-02", owned=True),
        Subscription("Humble Choice 2020-03", owned=True),
        Subscription("Humble Choice 2020-05", owned=False),  # active month
    ])


@pytest.mark.parametrize('subscription_plan_tier,has_choices', [
    pytest.param('lite', False, id='Lite'),
    pytest.param('basic', True, id='Basic'),
    pytest.param('premium', True, id='Premium'),
    pytest.param('premiumv1', True, id='Classic')
])
async def test_get_subscriptions_current_month_not_unlocked_yet(
        subscription_plan_tier, has_choices, api_mock, plugin
    ):
    """
    Technically only unlocked choice months are owned (locked are not already payed and can be canceled).
    But for user convenience plugin marks month as owned if it *is going to* be unloacked (if not cancelled untill last Friday).
    Without this, Galaxy won't display games until user manualy select current month as owned.
    This would be annoying, as a new subscription month happen... well every month.
    """
    subscription_state = json.loads("""
    {
      "currentlySkippingContentHumanName": null,
      "currentlySkippingContentMachineName": null,
      "perksStatus": "active",
      "monthlyNewestOwnedContentMachineName": "january_2020_choice",
      "willReceiveFutureMonths": true,
      "monthlyOwnsActiveContent": false,
      "lastSkippedContentMachineName": null,
      "isPaused": false,
      "wasPaused": false,
      "monthlyOwnsAnyContent": true
    }
    """)
    part_of_subscription_webpack_content = {
        "userSubscriptionPlan": {
            "tier": f"{subscription_plan_tier}",
            "human_name": "Month-to-Month Basic Plan",  # for now hardcoded from basic plan
            "length": 1,
            "machine_name": "monthly_v2_basic",  # for now hardcoded from basic plan
            "pricing|money": {
                "currency": "EUR",
                "amount": 13.99
            }
        },
        "user_max_reward_amount": 10,
        "subscriptionJoinDate|datetime": "2019-07-18T13:58:14.730512",
        "productIsChoiceless": False,
        "showSubsV3": None,
        "subscriptionExpires|datetime": "2020-05-02T17:00:00",
        "isEuCountry": True,
        "payEarlyOptions": {
            "activeContentStart|datetime": "2020-05-02T17:00:00",
            "productMachineName": "may_2020_choice"
        },
        "contentChoiceOptions": {
            "contentChoiceData": "{}",  # redacted a big object
            "isActiveContent": True,
            "title": "May 2020",
            "productUrlPath": "may-2020",
            "usesChoices": True,
            "canRedeemGames": True,
            "productMachineName": "may_2020_choice"
        }
    }
    content_choice_options = [
        {'contentChoiceData': Mock(dict), 'gamekey': Mock(str), 'productMachineName': 'april_2020_choice', 'isActiveContent': False}
    ]
    api_mock.get_user_subscription_state.return_value = subscription_state
    api_mock.get_subscriber_hub_data.return_value = part_of_subscription_webpack_content
    api_mock.get_subscription_products_with_gamekeys = MagicMock(return_value=aiter(content_choice_options))

    res = await plugin.get_subscriptions()

    assert_contains(res, [
        Subscription("Humble Choice 2020-04", owned=True),
        Subscription("Humble Choice 2020-05", owned=has_choices),
    ])
    assert api_mock.get_choice_marketing_data.call_count == 0


async def test_get_subscriptions_current_month_not_unlocked_yet__cant_fetch_early_unlock(
    api_mock, plugin
):
    subscription_state = json.loads("""
    {
      "currentlySkippingContentHumanName": null,
      "currentlySkippingContentMachineName": null,
      "perksStatus": "active",
      "monthlyNewestOwnedContentMachineName": "january_2020_choice",
      "willReceiveFutureMonths": true,
      "monthlyOwnsActiveContent": false,
      "lastSkippedContentMachineName": null,
      "isPaused": false,
      "wasPaused": false,
      "monthlyOwnsAnyContent": true
    }
    """)
    part_of_subscription_webpack_content = {
        "UNEXPECTED": "CONTENT"
    }
    content_choice_options = [
        {'contentChoiceData': Mock(dict), 'gamekey': Mock(str), 'productMachineName': 'april_2020_choice', 'isActiveContent': False}
    ]
    api_mock.get_user_subscription_state.return_value = subscription_state
    api_mock.get_subscriber_hub_data.return_value = part_of_subscription_webpack_content
    api_mock.get_subscription_products_with_gamekeys = MagicMock(return_value=aiter(content_choice_options))
    
    res = await plugin.get_subscriptions()
    assert_contains(res, [
        Subscription("Humble Choice 2020-04", owned=True),
        Subscription("Humble Choice 2020-05", owned=False),
    ])
    assert api_mock.get_choice_marketing_data.call_count == 1


async def test_get_subscription_perks(plugin, api_mock):
    subscription_state_excerpt = json.loads("""
    {
      "perksStatus": "active",
      "monthlyNewestOwnedContentMachineName": "march_2020_choice",
      "monthlyOwnsAnyContent": true
    }
    """)
    content_choice_options = [
        # hack: define an active month here to avoid mocking ActiveMonthResolver
        {'contentChoiceData': Mock(dict), 'productMachineName': 'april_2020_choice', 'isActiveContent': True}
    ]
    api_mock.get_user_subscription_state.return_value = subscription_state_excerpt
    api_mock.get_subscription_products_with_gamekeys = MagicMock(return_value=aiter(content_choice_options))

    res = await plugin.get_subscriptions()

    assert_contains(res, [
        Subscription("Humble Games Collection", owned=True),
        Subscription("Humble Vault", owned=True),
    ])
