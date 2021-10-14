import typing as t
import json
import datetime

from model.game import Key
from model.types import HP, DeliveryMethod, Tier


Timestamp = float


def datetime_parse(dt: str) -> Timestamp:
    return Timestamp(datetime.datetime.fromisoformat(dt).timestamp())


def _now_time() -> Timestamp:
    return Timestamp(datetime.datetime.now().timestamp())


class UserSubscriptionInfo:
    def __init__(self, data: dict) -> None:
        self._data = data
    
    @property
    def user_plan(self) -> "UserSubscriptionPlan":
        return UserSubscriptionPlan(self._data["userSubscriptionPlan"])

    @property
    def active_content_product_machine_name(self) -> str:
        return self._data["payEarlyOptions"]["productMachineName"]

    @property
    def active_content_start(self) -> Timestamp:
        return datetime_parse(self._data["payEarlyOptions"]["activeContentStart|datetime"])

    @property
    def subcription_join_date(self) -> Timestamp:
        return datetime_parse(self._data["subscriptionJoinDate|datetime"])

    @property
    def subscription_expires(self) -> Timestamp:
        return datetime_parse(self._data["subscriptionExpires|datetime"])
    
    def subscription_expired(self) -> bool:
        return _now_time() > self.subscription_expires


class UserSubscriptionPlan:
    """
    {
        "tier": "premiumv1",
        "human_name": "Month-to-Month Classic Plan",
        "length": 1,
        "machine_name": "monthly_basic",
        "pricing|money": {"currency": "USD", "amount": 12.0}
    }
    """
    def __init__(self, data: dict):
        self.tier = Tier(data['tier'])
        self.machine_name = data['machine_name']
        self.human_name = data['human_name']


class ChoiceMonth:
    """Below example of month from `data['monthDetails']['previous_months']`
    {
        "additional_items_text": "DiRT Rally 2.0 + 3 DLCs, Street Fighter V, Bad North: Jotunn Edition, Trailmakers, Unrailed!, Whispers of a Machine, Them's Fightin' Herds, Mages of Mystralia, and GRIP + 1 DLC",
        "machine_name": "january_2020_choice",  # also in active_month
        "short_human_name": "January 2020",  # also in active_month
        "image_human_names": {
          "grip": "GRIP + 1 DLC",
          "..."
        },
        "month_string": "February",  # also in active_month
        "early_unlock_logos": [
          "https://hb.imgix.net/9a6a6...",
        ],
        "image_grid": {
          "width": 308,
          "size_override": null,
          "displayitem_image_info": {
            "grip": {
              "standard_url": "https://hb.imgix.net/a8589a...",
              "blocked_territories": [],
              "allowed_territories": null,
              "hide_from_hero_tile": null,
              "retina_url": "https://hb.imgix.net/a858...",
            },
            "...": {}
          },
          "height": 177
        },
        "charity_logo": "https://hb.imgix.net/ca5...",  # also in active month
        "monthly_product_page_url": "/subscription/january-2020",  # also in active month
        "grid_display_order": [
          "middleearth_shadowofwar",
          "graveyardkeeper",
          "..."
        ],
        "charity_name": "Girls Inc.",  # also in active month
        "item_count": 12,
        "msrp|money": {
          "currency": "EUR",
          "amount": 302
        },
        "charity_video_url": "ngmfbcEktXU"  # also in active month
      },
    """
    def __init__(self, data: dict, is_active: bool = False):
        self._data = data
        self.is_active: bool = is_active
        self.machine_name: str = data['machine_name']
        self.short_human_name: str = data['short_human_name']
        self.monthly_product_page_url: str = data['monthly_product_page_url']
    
    def __repr__(self) -> str:
        return json.dumps(self._data, indent=4)

    @property
    def last_url_part(self):
        return self.monthly_product_page_url.split('/')[-1]


class Section():
    """Contains information about montly game"""
    def __init__(self, data: dict):
        self.id = data['id']
        self.human_name = data['human_name']
        self.delivery_methods: t.List[DeliveryMethod] = [
            DeliveryMethod(m) for m in data['delivery_methods']
        ]
        self.platforms: t.List[HP] = [
            HP(p) for p in data['platforms']
        ]


class ContentChoice:
    """
    Unexposed:
    - genres: List[str]
    - description: str
    - developers: List[str]
    - msrp|money: object
    - image: str (link)
    - carousel_content: object
    """
    def __init__(self, id: str, data: dict):
        self.id = id
        self.title = data['title']
        self.display_item_machine_name = data['display_item_machine_name']
        self.tpkds = [
            Key(tpkd) for tpkd in data.get('tpkds', [])
        ]
        self.delivery_methods: t.List[DeliveryMethod] = [
            DeliveryMethod(m) for m in data['delivery_methods']
        ]
        self.platforms: t.List[HP] = [
            HP(p) for p in data['platforms']
        ]


class Extras:
    def __init__(self, data: dict):
        self.human_name: str = data['human_name']
        self.icon_path: t.Optional[str] = data.get('icon_path')
        self.machine_name: str = data['machine_name']
        self.class_: str = data['class']
        self._types: t.List[str] = data['types']


class ContentChoiceOptions:
    def __init__(self, data: dict):
        self.MAX_CHOICES: int = data['MAX_CHOICES']
        self.gamekey: t.Optional[str] = data.get('gamekey')
        self.is_active_content: bool = data['isActiveContent']
        self.product_url_path: str = data['productUrlPath']
        self.includes_any_uplay_tpkds: t.Optional[bool] = data.get('includesAnyUplayTpkds')
        self.is_choice_tier: t.Optional[bool] = data.get('isChoiceTier')  # no in active month
        self.product_machine_name: str = data['productMachineName']
        self.title: str = data['title']

        self.unlocked_content_events: t.Optional[t.List[str]] = data.get('unlockedContentEvents')

        content_choice_data = data['contentChoiceData']

        # Since August 2020 there is no simple 'initial' key, games may be stored under different keys:
        # 'initial-without-order'  # for not yet unlocked months
        # 'initial-classic',       # classic plan
        # 'initial-basic'          # XXX to be confirmed
        # 'initial-premium'        # XXX to be confirmed
        try:
            initial_key = next(filter(lambda x: x.startswith('initial'), content_choice_data))
        except StopIteration:
            raise KeyError('initial key or similar not found in contentChoiceData')
        initial = content_choice_data[initial_key]

        self.content_choices: t.List[ContentChoice] = [
            ContentChoice(id, c) for id, c
            in initial['content_choices'].items()
        ]
        self.extrases: t.List[Extras] = [
            Extras(extras) for extras
            in content_choice_data['extras']
        ]
        self._content_choices_made = data.get('contentChoicesMade')

    @property
    def content_choices_made(self) -> t.List[str]:
        if self._content_choices_made:
            return self._content_choices_made['initial']['choices_made']
        return []

    @property
    def remained_choices(self) -> int:
        if self._content_choices_made is None:
            return self.MAX_CHOICES
        return self.MAX_CHOICES - len(self._content_choices_made)


class ContentMonthlyOptions:
    """
    "machine_name": "september_2019_monthly",
    "highlights": [
        "8 Games",
        "$179.00 Value"
    ],
    "order_url": "/downloads?key=Ge882ERvybaawmWd",
    "short_human_name": "September 2019",
    "hero_image": "https://hb.imgix.net/a25aa69d4c827d42142d631a716b3fbd89c15733.jpg?auto=compress,format&fit=crop&h=600&w=1200&s=789fedc066299f3d3ed802f6f1e55b6f",
    "early_unlock_string": "Slay the Spire and Squad (Early Access)"
    """
    def __init__(self, data: dict):
        for k, v in data.items():
            setattr(self, k, v)


class MontlyContentData:
    """
    "webpack_json": {
        "isEuCountry": bool
        "baseSubscriptionPrice|money": {...}
        "exchangeRates": Dict[str, float]
        "csrfInput": str
        "user_max_reward_amount": int
        "showSingleSignOn": true,
        "userOptions": {...},
        "userSubscriptionPlan":  {...}
        "showSingleSignOn": bool
        "referralModelData": {...}
    }
    "navbarOptions": {
      "product_human_name": "August 2019 Humble Monthly",
      "price_to_subscribe": {
        "currency": "EUR",
        "amount": 17.99
      },
      "sections": [
      {
          "human_name": "Kingdom Come: Deliverance",
          "delivery_methods": [
            "epic",
            "steam"
          ],
          "id": "kingdomcome_deliverance",
          "platforms": [
            "windows"
          ]
      }
      ]
    }
    """
    def __init__(self, data: dict):
        base = data['webpack_json']
        self.user_options: dict = base['userOptions']
        plan = base['userSubscriptionPlan']
        self.user_subscription_plan = UserSubscriptionPlan(plan) if plan else None

        content = data['navbarOptions']
        self.product_human_name: str = content['product_human_name']
        self.sections: t.List[Section] = [
            Section(s) for s in content['sections']
        ]


class ChoiceContentData:
    """
        "isEuCountry": bool
        "baseSubscriptionPrice|money": {...}
        "exchangeRates": Dict[str, float]
        "csrfInput": str
        "user_max_reward_amount": int
        "showSingleSignOn": true,
        "userOptions": {...},
        "userSubscriptionPlan":  {...}
        "payEarlyOptions": {...}
        "contentChoiceOptions": {...}
    }
    """
    def __init__(self, data: dict):
        self.user_options: dict = data['userOptions']
        plan = data['userSubscriptionPlan']
        self.user_subscription_plan = UserSubscriptionPlan(plan) if plan else None
        self.pay_early_options: dict = data['payEarlyOptions']
        self.content_choice_options = ContentChoiceOptions(data['contentChoiceOptions'])

    @property
    def active_content_start(self) -> t.Optional[Timestamp]:
        try:
            dt = self.pay_early_options['activeContentStart|datetime']
        except KeyError:
            return None
        return datetime_parse(dt)
