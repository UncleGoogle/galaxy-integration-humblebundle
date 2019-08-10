from humblegame import Subproduct
from consts import GAME_PLATFORMS, HP


def test_humblegame_properties_overgrowth(overgrowth):
    for sub_data in overgrowth['subproducts']:
        sub = Subproduct(sub_data)
        sub.human_name
        sub.machine_name
        sub.license
        for platform, download_structs in sub.downloads.items():
            assert platform in set(HP)
            for dw_struct in download_structs:
                dw_struct.web
                dw_struct.bittorrent
                dw_struct.human_size
        assert not set(sub.downloads).isdisjoint(GAME_PLATFORMS)


def test_humblegame_properties_access(orders):
    for order in orders:
        for sub_data in order['subproducts']:
            sub = Subproduct(sub_data)
            sub.human_name
            sub.machine_name
            sub.license
            for platform, download_structs in sub.downloads.items():
                assert platform in set(HP)
                for dw_struct in download_structs:
                    dw_struct.web
                    dw_struct.bittorrent
                    dw_struct.human_size
