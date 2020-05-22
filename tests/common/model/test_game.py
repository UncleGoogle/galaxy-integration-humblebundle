from model.game import Subproduct, Key, KeyGame
from model.types import GAME_PLATFORMS, HP


def test_game_properties_overgrowth(overgrowth):
    for sub_data in overgrowth['subproducts']:
        sub = Subproduct(sub_data)
        sub.human_name
        sub.machine_name
        sub.license
        for platform, download in sub.downloads.items():
            assert platform in set(HP)
            for dw_struct in download.download_struct:
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
            for platform, download in sub.downloads.items():
                assert platform in set(HP)
                for dw_struct in download.download_struct:
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


def test_key_key_games_one_game():
    """Most common case where 1 key == 1 game"""
    key = Key({
        "machine_name": "ww",
        "human_name": "The Witcher",
        "key_type_human_name": "Steam Key"
    })
    assert key.key_games == [KeyGame(key, "ww", "The Witcher (Steam Key)")]


def test_key_key_game_data():
    tpks = {
        "machine_name": "ww",
        "human_name": "The Witcher, The Witcher 2"
    }
    key = Key(tpks)
    assert tpks == KeyGame(key, 'ww', 'sth')._data


def test_key_split_key_games():
    tpks = {
        "machine_name": "sega",
        "human_name": "Alpha Protocol, Company of Heroes, Rome: Total War, Hell Yeah! Wrath of the Dead Rabbit",
    }
    key = Key(tpks)
    assert key.key_games == [
        KeyGame(key, "sega_0", "Alpha Protocol"),
        KeyGame(key, "sega_1", "Company of Heroes"),
        KeyGame(key, "sega_2", "Rome: Total War"),
        KeyGame(key, "sega_3", "Hell Yeah! Wrath of the Dead Rabbit")
    ]


def test_key_game_human_name_changed():
    tpks = {
        'machine_name': 'tor',
        'human_name': 'Tor',
        'key_type_human_name': 'Steam Key'
    }
    assert KeyGame(Key(tpks), 'tor', 'Tor').human_name == 'Tor (Steam Key)'


def test_key_game_human_name_not_changed():
    tpks = {
        'machine_name': 'tor',
        'human_name': 'Tor Steam',
        'key_type_human_name': 'Steam'
    }
    assert KeyGame(Key(tpks), 'tor', 'Tor Steam').human_name == 'Tor Steam'

