import typing as t

from galaxy.api.errors import UnknownBackendResponse

from webservice import AuthorizedHumbleAPI, WebpackParseError
from model.subscription import UserSubscriptionInfo
from model.types import Tier


class ActiveMonthInfoByUser(t.NamedTuple):
    machine_name: str
    '''
    Treats two bussines cases the same way:
    having active month content AND not owning yet, but having payment scheduled
    https://support.humblebundle.com/hc/en-us/articles/217300487-Humble-Choice-Early-Unlock-Games
    '''
    is_or_will_be_owned: bool


ActiveMonthInfoFetchStrategy = t.Callable[[AuthorizedHumbleAPI], t.Awaitable[ActiveMonthInfoByUser]]


class _CantFetchActiveMonthInfo(Exception):
    pass


class ActiveMonthResolver():
    def __init__(self, has_active_subscription: bool) -> None:
        if has_active_subscription:
            fetch_strategy = _get_ami_from_subscriber_fallbacking_to_marketing
        else:
            fetch_strategy = _get_ami_from_marketing
        self._fetch_strategy: ActiveMonthInfoFetchStrategy = fetch_strategy

    async def resolve(self, api: AuthorizedHumbleAPI) -> ActiveMonthInfoByUser:
        return await self._fetch_strategy(api)

    
async def _get_ami_from_subscriber_fallbacking_to_marketing(api: AuthorizedHumbleAPI) -> ActiveMonthInfoByUser:
    try:
        return await _get_ami_from_subscriber(api) 
    except _CantFetchActiveMonthInfo:
        return await _get_ami_from_marketing(api)


async def _get_ami_from_subscriber(api: AuthorizedHumbleAPI) -> ActiveMonthInfoByUser:
    try:
        raw = await api.get_subscriber_hub_data()
        subscriber_hub = UserSubscriptionInfo(raw)
        machine_name = subscriber_hub.pay_early_options.active_content_product_machine_name
        marked_as_owned = subscriber_hub.user_plan.tier != Tier.LITE
    except (WebpackParseError, KeyError, AttributeError, ValueError) as e:
        msg = f"Can't get info about not-yet-unlocked subscription month: {e!r}"
        raise _CantFetchActiveMonthInfo(msg)
    else:
        return ActiveMonthInfoByUser(machine_name, marked_as_owned)


async def _get_ami_from_marketing(api: AuthorizedHumbleAPI) -> ActiveMonthInfoByUser:
    try:
        marketing_data = await api.get_choice_marketing_data()
        machine_name = marketing_data['activeContentMachineName']
    except (KeyError, UnknownBackendResponse) as e:
        raise UnknownBackendResponse(e)
    else:
        return ActiveMonthInfoByUser(machine_name, False)
