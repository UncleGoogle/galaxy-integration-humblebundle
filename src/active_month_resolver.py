import abc
import logging
import typing as t

from webservice import AuthorizedHumbleAPI, WebpackParseError
from model.subscription import UserSubscriptionInfo
from model.types import Tier


logger = logging.getLogger(__name__)


MachineName = str
IsOwned = bool
ActiveMonthStrategy = t.Callable[[AuthorizedHumbleAPI], t.Tuple[MachineName, IsOwned]]


class ActiveMonthResolver():
    def __init__(self, strategy: ActiveMonthStrategy) -> None:
        self._strategy = strategy
    
    def change_strategy(self, strategy: ActiveMonthStrategy) -> None:
        self._strategy = strategy
    
    async def resolve(self, api: AuthorizedHumbleAPI) -> t.Tuple[MachineName, IsOwned]:
        return await self._strategy(api)


async def get_active_month_info_for_subscriber(api: AuthorizedHumbleAPI) -> None:
    """
    Useful to fetch info about active month for Choice subscribers who not used "Early Unlock" yet:
    https://support.humblebundle.com/hc/en-us/articles/217300487-Humble-Choice-Early-Unlock-Games
    """
    try:
        raw = await api.get_subscriber_hub_data()
        subscriber_hub = UserSubscriptionInfo(raw)
        self._machine_name = subscriber_hub.pay_early_options.active_content_product_machine_name
        self._marked_as_owned = subscriber_hub.user_plan.tier != Tier.LITE
    except (WebpackParseError, KeyError, AttributeError, ValueError) as e:
        logger.error(f"Can't get info about not-yet-unlocked subscription month: {e!r}")
    else:
        early_unlock_info_fetch_success = True

            if not early_unlock_info_fetch_success:
                # for those who have no "choices" as a potential discovery of current choice games
                active_month_machine_name = await self._find_active_month_machine_name()
                active_month_marked_as_owned = False


class ActiveMonthContext():
    def __init__(self, strategy: ActiveMonthResolverStrategy) -> None:
        self._strategy = strategy

