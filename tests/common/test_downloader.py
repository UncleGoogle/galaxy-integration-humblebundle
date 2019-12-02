import pytest

from humbledownloader import HumbleDownloadResolver
from model.game import Subproduct, TroveGame
from consts import HP, BITNESS, PlatformNotSupported


@pytest.mark.parametrize("platform,bitness", [(HP.WINDOWS, BITNESS.B64), (HP.WINDOWS, BITNESS.B32), (HP.MAC, BITNESS.B64)])
def test_any_download_found(orders, get_troves, platform, bitness):
    """Test choosing proper download"""
    download_resolver = HumbleDownloadResolver(platform, bitness)

    for order in orders:
        for sub_data in order['subproducts']:
            sub = Subproduct(sub_data)
            if not sub.os_compatibile(platform):
                continue
            try:
                download_resolver(sub) 
            except NotImplementedError as e:
                pytest.fail('Unresolved download: ' + str(e))

    for trove_data in get_troves(from_index=0):
        trove = TroveGame(trove_data)
        if not trove.os_compatibile(platform):
            continue
        download_resolver(trove)


def test_windows_bitness_priority():
    subproduct_data = {
        'machine_name': 'test',
        'human_name': 'TEST',
        'downloads': [
            {
                'platform': 'windows',
                'machine_name': 'test_dw',
                'download_struct': [
                    { 'name': '32-bit' },
                    { 'name': '64-bit' }
                ]
            }
        ]
    }
    sub = Subproduct(subproduct_data)
    download = HumbleDownloadResolver(HP.WINDOWS, BITNESS.B64)(sub)
    assert download.name == '64-bit'
    download = HumbleDownloadResolver(HP.WINDOWS, BITNESS.B32)(sub)
    assert download.name == '32-bit'