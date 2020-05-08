import typing as t
import datetime
import enum

from model.game import HumbleGame, Key
from model.types import HP, DeliveryMethod


class UserSubscriptionPlan:
    """
    "human_name": "Month-to-Month Classic Plan",
    "length": 1,
    "machine_name": "monthly_basic",
    "pricing|money": {
        "currency": "USD",
        "amount": 12
        }
    "user_max_reward_amount": 20
    """
    def __init__(self, data: dict):
        self.human_name: str = data['human_name']
        self.machine_name: str = data['machine_name']
        self.length: int  = data['length']



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
        self.icon_path: str = data['icon_path']
        self.machine_name: str = data['machine_name']
        self.class_: str = data['class']
        self._types: t.List[str] = data['types']


class ContentChoiceOptions:
    def __init__(self, data: dict):
        self.MAX_CHOICES: int = data['MAC_CHOICES']
        self.gamekey: str = data['gamekey']
        self.is_active_content: bool = data['isActiveContent']
        self.product_url_path: str = data['productUrlPath']
        self.includes_any_uplay_tpkds: bool = data['includesAnyUplayTpkds']
        self.is_choice_tier: bool = data['isChoiceTier']
        self.product_machine_name: str = data['productMachineName']

        self.unlocked_conntent_event: t.Optional[str] = data.get('unlockedContentEvents')

        self.title: str = data['contentChoiceData']['initial']['title']
        self.content_choices: t.List[ContentChoice] = [
            ContentChoice(id, c)
            for id, c
            in data['contentChoiceData']['initial']['contentChoices'].items()
        ]
        self.extras: t.List[Extras] = [
            Extras(extras) for extras
            in data['contentChoiceData']['extras']
        ]

    @property
    def machine_name(self) -> str:
        return self.product_machine_name

    @property
    def human_name(self) -> str:
        return self.title


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
        self.user_subscription_plan = UserSubscriptionPlan(base['userSubscriptionPlan'])

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
        self.user_subscription_plan = UserSubscriptionPlan(data['userSubscriptionPlan'])
        self.pay_early_option: dict = data['payEarlyOptions']
        self.content_choice_options = ContentChoiceOptions(data['contentChoiceOptions'])

    @property
    def active_from(self) -> t.Optional[datetime.datetime]:
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
        return self.content_choice_options.human_name
