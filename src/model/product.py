from typing import Optional


class JsonDataclass:
    def __init__(self, data: dict):
        self._data = data


class Product(JsonDataclass):
    """
        machine_name: str
        category: str
        human_name: str
        amount_spent: float
        empty_tpkds: dict
        post_purchase_text: str
        partial_gift_enabled: bool = False
    """
    def __init__(self, data: dict):
        self._data = data

    @property
    def category(self):
        return self._data['category']

    @property
    def bundle_type(self) -> Optional[str]:
        if self.category != 'bundle':
            return None
        mn = self._data["machine_name"]
        return mn.split('_')[-1]
