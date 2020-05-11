import typing as t
import datetime
import enum

from model.game import HumbleGame, Key
from model.types import HP, DeliveryMethod


class ChoiceMonth:
    """
    {
        "additional_items_text": "DiRT Rally 2.0 + 3 DLCs, Street Fighter V, Bad North: Jotunn Edition, Trailmakers, Unrailed!, Whispers of a Machine, Them's Fightin' Herds, Mages of Mystralia, and GRIP + 1 DLC",
        "machine_name": "january_2020_choice",
        "short_human_name": "January 2020",
        "image_human_names": {
          "grip": "GRIP + 1 DLC",
          "graveyardkeeper": "Graveyard Keeper",
          "..."
        },
        "month_string": "February",
        "early_unlock_logos": [
          "https://hb.imgix.net/9a6a64a968664683d0948c03012adb779c5d59e1.png?auto=compress,format&w=650&s=dd323d59e5db2a4ce5e103e70ff59c70"
        ],
        "image_grid": {
          "width": 308,
          "size_override": null,
          "displayitem_image_info": {
            "grip": {
              "standard_url": "https://hb.imgix.net/a8589ac1102547877319717a3a37b02bfc1b6341.jpeg?auto=compress,format&dpr=1&fit=clip&h=177&w=308&s=812e5702ffd184571eab42d45f5bb73d",
              "blocked_territories": [],
              "allowed_territories": null,
              "hide_from_hero_tile": null,
              "retina_url": "https://hb.imgix.net/a8589ac1102547877319717a3a37b02bfc1b6341.jpeg?auto=compress,format&dpr=2&fit=clip&h=177&w=308&s=fd99859c52ac37a864f106c831d433d2"
            },
            "...": {}
          },
          "height": 177
        },
        "charity_logo": "https://hb.imgix.net/ca5838784ea6a6e1f60ee1ef183036548384e75d.png?auto=compress,format&fit=clip&h=165&w=260&s=b58e3c3db87a698ae2563489725d836b",
        "monthly_product_page_url": "/subscription/january-2020",
        "grid_display_order": [
          "middleearth_shadowofwar",
          "graveyardkeeper",
          "..."
        ],
        "charity_name": "Girls Inc.",
        "item_count": 12,
        "msrp|money": {
          "currency": "EUR",
          "amount": 302
        },
        "charity_video_url": "ngmfbcEktXU"
      },
    """
    def __init__(self, data: dict):
        self.machine_name: str = data['machine_name']
        self.short_human_name: str = data['short_human_name']
        self.item_count: int = data['item_count']


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
            Key(tpkd) for tpkd in data['tpkds']
        ]
        self.delivery_methods: t.List[DeliveryMethod] = [
            DeliveryMethod(m) for m in data['delivery_methods']
        ]
        self.platforms: t.List[HP] = [
            HP(p) for p in data['platforms']
        ]

    @property
    def machine_name(self):
        return self.id

    @property
    def human_name(self):
        return self.title


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
        self.extras: t.List[Extras] = [
            Extras(extras) for extras
            in data['contentChoiceData']['extras']
        ]
        self._content_choices_made = data.get('contentChoicesMade')

    @property
    def content_choices_made(self) -> t.Optional[t.List[str]]:
        if self._content_choices_made:
            return self._content_choices_made['initial']['choices_made']
        return None


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

    @property
    def human_name(self) -> str:
        return self.product_human_name


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
        self.pay_early_option: dict = data['payEarlyOptions']
        self.content_choice_options = ContentChoiceOptions(data['contentChoiceOptions'])

    @property
    def early_unlock_since(self) -> t.Optional[datetime.datetime]:
        try:
            iso = self.pay_early_option['activeContentStart|datetime']
        except KeyError:
            return None
        return datetime.datetime.fromisoformat(iso)

    @property
    def machine_name(self) -> str:
        return self.pay_early_option['productMachineName']

    @property
    def human_name(self) -> str:
        return self.content_choice_options.title
