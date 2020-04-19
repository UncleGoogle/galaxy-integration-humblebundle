from humbledownloader import HumbleDownloadResolver
from model.download import SubproductDownload
from consts import BITNESS


def test_download_resolver_for_bitness():
    data = {
        'platform': 'windows',
        'machine_name': 'test_dw',
        'download_struct': [
            { 'name': '32-bit' },
            { 'name': '64-bit' }
        ]
    }
    sub = SubproductDownload(data)
    download = HumbleDownloadResolver(BITNESS.B64)(sub)
    assert download.name == '64-bit'
    download = HumbleDownloadResolver(BITNESS.B32)(sub)
    assert download.name == '32-bit'
