import pytest
import json

from humbledownloader import HumbleDownloadResolver
from model.game import Subproduct, TroveGame
from consts import HP, PlatformNotSupported


@pytest.mark.parametrize("platform", [HP.WINDOWS, HP.MAC])
@pytest.mark.parametrize("bitness", [64, 32])
def test_is_any_download_windows(orders, get_troves, platform, bitness):
    if platform == HP.MAC and bitness == 32:
        return  # no 32bit macs now
    download_resolver = HumbleDownloadResolver(platform, bitness)

    for order in orders:
        for sub_data in order['subproducts']:
            sub = Subproduct(sub_data)
            try:
                download_resolver(sub) 
            except PlatformNotSupported:
                pass  # it happens
            except NotImplementedError as e:
                pytest.fail('Unresolved download: ' + e)

    for trove_data in get_troves(from_index=0):
        trove = TroveGame(trove_data)
        try:
            download_resolver(trove) 
        except PlatformNotSupported:
            pass  # it happens
