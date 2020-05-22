import typing as t
import datetime

from model.game import Key
from model.types import HP, DeliveryMethod


class ChoiceMarketingData:
    """Custom class based on `webpack-choice-marketing-data['monthDetails'] from https://www.humblebundle.com/subscription
    {
        "monthDetails": {
            "previous_months": [],
            "active_month": {}
        },
        "userOptions": {
            "email": str,
            ...
        },
        ...
    }
    """
    def __init__(self, data: dict):
        self.user_options = data['userOptions']
        self.month_details = [
            ChoiceMonth(data['monthDetails']['active_month'], is_active=True)
        ] + [
            ChoiceMonth(month, is_active=False)
            for month in data['monthDetails']['previous_months']
        ]


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
        self.is_active: bool = is_active
        self.machine_name: str = data['machine_name']
        self.short_human_name: str = data['short_human_name']
        self.monthly_product_page_url: str = data['monthly_product_page_url']

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

        self.content_choices: t.List[ContentChoice] = [
            ContentChoice(id, c) for id, c
            in data['contentChoiceData']['initial']['content_choices'].items()
        ]
        self.extrases: t.List[Extras] = [
            Extras(extras) for extras
            in data['contentChoiceData']['extras']
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
        self.user_subscription_plan: t.Optional[dict] = base['userSubscriptionPlan']

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
        self.user_subscription_plan: t.Optional[dict] = data['userSubscriptionPlan']
        self.pay_early_options: dict = data['payEarlyOptions']
        self.content_choice_options = ContentChoiceOptions(data['contentChoiceOptions'])

    @property
    def active_content_start(self) -> t.Optional[datetime.datetime]:
        try:
            iso = self.pay_early_options['activeContentStart|datetime']
        except KeyError:
            return None
        return datetime.datetime.fromisoformat(iso)
