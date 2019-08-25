from model.game import Subproduct, TroveGame, Key
from consts import GAME_PLATFORMS, HP


def test_game_properties_overgrowth(overgrowth):
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


def test_game_properties_access(orders):
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


def test_key_properties(origin_bundle_order):
    all_tpks = origin_bundle_order['tpkd_dict']['all_tpks']
    for key_data in all_tpks:
        key = Key(key_data)
        key.key_type
        key.key_val
        key.downloads
        key.in_galaxy_format()


def test_base_name():
    base_name = 'testgame'
    assert base_name == TroveGame({'machine_name': 'testgame_trove'}).base_name
    assert base_name == Subproduct({'machine_name': 'testgame'}).base_name
    assert 'a_b_cde' == Subproduct({'machine_name': 'a_b_cde'}).base_name
    assert base_name == Key({
        'key_type': 'uplay',
        'machine_name': 'testgame_uplay'
    }).base_name
    assert base_name == Key({
        'key_type': 'steam',
        'machine_name': 'testgame_steam'
    }).base_name
    assert 'jbundle_testgame' == Key({
        'key_type': 'origin',
        'machine_name': 'jbundle_testgame_origin'
    }).base_name
