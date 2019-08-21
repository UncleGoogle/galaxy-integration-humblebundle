import pytest
import json

from model.product import Product


@pytest.fixture
def software_photo():
    return json.loads(R'''{
         "category":"bundle",
        "machine_name":"professionalphotography_softwarebundle",
        "empty_tpkds":{},
        "post_purchase_text":"",
        "human_name":"Humble Software Bundle: Professional Photography",
        "partial_gift_enabled":true
        }''')


@pytest.fixture
def storefront_prod():
    return json.loads(R'''{
        "category":"storefront",
        "machine_name":"tropico4_freegame",
        "empty_tpkds":{},
        "post_purchase_text":"<p>\r\n<strong>Note: You must redeem your free <em>Tropico 4</em> key by 10AM Pacific on Saturday, September 17, 2016!</strong> Immediately after 10AM Pacific on September 17, the code will magically vanish as if it were just a figment of your imagination, leaving this cryptic message behind in its wake.\r\n<br><br>\r\nIf you like <em>Tropico 4</em>, you should also <a href=\"https://www.humblebundle.com/store/promo/kalypso/\" target=\"_blank\">check out these other great Kalypso Media titles on sale!</a></b><br>\r\n<br>\r\n</p>",
        "human_name":"Tropico 4",
        "partial_gift_enabled":false
        }''')


def test_bundle_type(software_photo, storefront_prod):
    prod = Product(software_photo)
    not_bundle_prod = Product(storefront_prod)
    assert prod.category == 'bundle'
    assert prod.bundle_type == 'softwarebundle'
    assert not_bundle_prod.category == 'storefront'
    assert not_bundle_prod.bundle_type == None
