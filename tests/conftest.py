import pytest
import pathlib
import json
import asyncio
from unittest.mock import MagicMock

from plugin import HumbleBundlePlugin


@pytest.fixture
async def plugin_mock():
    plugin = HumbleBundlePlugin(MagicMock(), MagicMock(), "handshake_token")
    plugin._check_installed_task.cancel()
    plugin._check_statuses_task.cancel()

    yield plugin

    plugin.shutdown()
    await asyncio.sleep(0)


@pytest.fixture
def orders():
    path = pathlib.Path(__file__).parent / 'data' / 'orders.json'
    with open(path, 'r') as f:
        return json.load(f)


@pytest.fixture
def overgrowth():
    return json.loads(R'''
    {
    "amount_spent": 29.95,
    "product": {
        "category": "widget",
        "machine_name": "overgrowth",
        "empty_tpkds": {},
        "post_purchase_text": "Thanks for purchasing Overgrowth!  Be sure to keep track of updates and news here:\r\n<ul>\r\n  <li><a href=\"http://www.reddit.com/r/Overgrowth\">Subscribe to r/Overgrowth</a> (Reddit)</li>\r\n  <li><a href='http://www.facebook.com/Overgrowth'>Join our Facebook page</a></li>\r\n  <li><a href='http://twitter.com/Wolfire'>Follow @Wolfire on Twitter</a></li>\r\n  <li><a href='http://www.youtube.com/WolfireGames'>Subscribe to our YouTube channel</a></li>\r\n  <li><a href='http://feeds.wolfire.com/WolfireGames'>Get blog posts delivered</a> (email or RSS)</li>\r\n</ul>\r\n    Your order also comes with a complimentary copies of <a href='http://www.wolfire.com/receiver'>Receiver</a> and <a href=\"http://www.wolfire.com/llc\">Low Light Combat</a>!<br /><br />\r\n\r\nBe sure to join the Secret Preorder Forum with the box below to join the Overgrowth community and get access to community tools like the \"SUMLauncher\".",
        "human_name": "Overgrowth",
        "partial_gift_enabled": false
    },
    "gamekey": "XrCTukcAFwsh",
    "uid": "X2M9Z64T3YRGT",
    "created": "2012-10-10T19:25:27.523250",
    "missed_credit": null,
    "subproducts": [
        {
        "machine_name": "overgrowth",
        "url": "http://www.wolfire.com/overgrowth",
        "downloads": [
            {
            "machine_name": "overgrowth_linux",
            "platform": "linux",
            "download_struct": [
                {
                "uploaded_at": "2019-01-11T03:22:35.735991",
                "name": "Download",
                "url": {
                    "web": "https://dl.humble.com/wolfiregames/overgrowth-1.4.0_build-5584-linux64.zip?gamekey=XrCTukcAFwsh&ttl=1563893021&t=46b9a84ac7c864cf8fe263239a9978ae",
                    "bittorrent": "https://dl.humble.com/torrents/wolfiregames/overgrowth-1.4.0_build-5584-linux64.zip.torrent?gamekey=XrCTukcAFwsh&ttl=1563893021&t=3295590fac28bdeabba7baf5c4accc78"
                },
                "human_size": "7.6 GB",
                "file_size": 8207012480,
                "small": 0,
                "md5": "748f6888386d842193218c53396ac844"
                }
            ],
            "options_dict": {},
            "download_identifier": "",
            "android_app_only": false,
            "download_version_number": null
            },
            {
            "machine_name": "overgrowth_windows",
            "platform": "windows",
            "download_struct": [
                {
                "uploaded_at": "2019-01-10T23:33:03.308609",
                "name": "Patch",
                "url": {
                    "web": "https://dl.humble.com/wolfiregames/overgrowth-1.4.0_build-5584.zip?gamekey=XrCTukcAFwsh&ttl=1563893021&t=e22171338b7454a2ac50e018ede0d17b",
                    "bittorrent": "https://dl.humble.com/torrents/wolfiregames/overgrowth-1.4.0_build-5584.zip.torrent?gamekey=XrCTukcAFwsh&ttl=1563893021&t=60002f4d2d252bdd53dfe8a3d48ad75e"
                },
                "human_size": "413.5 MB",
                "file_size": 433584122,
                "small": 0,
                "md5": "40f16124359e462ad40ceb9bb0806ab6"
                },
                {
                "uploaded_at": "2019-01-11T02:07:27.164794",
                "name": "Download",
                "url": {
                    "web": "https://dl.humble.com/wolfiregames/overgrowth-1.4.0_build-5584-win64.zip?gamekey=XrCTukcAFwsh&ttl=1563893021&t=7f2263e7f3360f3beb112e58521145a0",
                    "bittorrent": "https://dl.humble.com/torrents/wolfiregames/overgrowth-1.4.0_build-5584-win64.zip.torrent?gamekey=XrCTukcAFwsh&ttl=1563893021&t=6403cdce9214306cc3a8fdfc6205526f"
                },
                "human_size": "7.6 GB",
                "file_size": 8140442729,
                "small": 0,
                "md5": "ad0e8c15f8dbef5d66b11935ef46f780"
                }
            ],
            "options_dict": {},
            "download_identifier": "",
            "android_app_only": false,
            "download_version_number": null
            },
            {
            "machine_name": "overgrowth_mac_E8cLL",
            "platform": "mac",
            "download_struct": [
                {
                "uploaded_at": "2019-01-11T02:32:22.117206",
                "name": "Download",
                "url": {
                    "web": "https://dl.humble.com/wolfiregames/overgrowth-1.4.0_build-5584-macosx.zip?gamekey=XrCTukcAFwsh&ttl=1563893021&t=5ade7954d8fc63bbe861932be538c07e",
                    "bittorrent": "https://dl.humble.com/torrents/wolfiregames/overgrowth-1.4.0_build-5584-macosx.zip.torrent?gamekey=XrCTukcAFwsh&ttl=1563893021&t=4a11fc885652fabe90c2b28342630318"
                },
                "human_size": "7.6 GB",
                "file_size": 8145041054,
                "small": 0,
                "md5": "391586e9b89d303bf0743de62eadd72f"
                }
            ],
            "options_dict": {},
            "download_identifier": "",
            "android_app_only": false,
            "download_version_number": null
            }
        ],
        "library_family_name": null,
        "payee": {
            "human_name": "Wolfire Games",
            "machine_name": "wolfiregames"
        },
        "human_name": "Overgrowth",
        "custom_download_page_box_html": "",
        "icon": "https://hb.imgix.net/f0efada7d3fb5ac8438abb18c9048e6f34cf3bf5.png?auto=format&s=9276237208d8ea0cf40ec7ac3b7119c2"
        },
        {
        "machine_name": "receiver",
        "url": "http://www.wolfire.com/receiver",
        "downloads": [
            {
            "machine_name": "receiver_mac_7xGAm",
            "platform": "mac",
            "download_struct": [
                {
                "uploaded_at": "2019-04-11T22:18:37.650487",
                "name": "Download",
                "url": {
                    "web": "https://dl.humble.com/wolfiregames/receiver_rc7_osx.zip?gamekey=XrCTukcAFwsh&ttl=1563893021&t=7fd3e7a0c75817b7c1c16436a2cfa33b",
                    "bittorrent": "https://dl.humble.com/torrents/wolfiregames/receiver_rc7_osx.zip.torrent?gamekey=XrCTukcAFwsh&ttl=1563893021&t=f36922c9d6b0d79d5a62939ff5f9acb2"
                },
                "timestamp": 1555021159,
                "human_size": "75.4 MB",
                "file_size": 79049021,
                "small": 0,
                "md5": "bee572fc266f5bc00c9e2da9f4ed1e90"
                }
            ],
            "options_dict": {},
            "download_identifier": null,
            "android_app_only": false,
            "download_version_number": null
            },
            {
            "machine_name": "receiver_linux",
            "platform": "linux",
            "download_struct": [
                {
                "sha1": "090012f4a1749023d2728d97fc1044a2b9cee59c",
                "name": "32-bit .tar.gz (beta)",
                "url": {
                    "web": "https://dl.humble.com/receiver_rc7_linux_32.tar.gz?gamekey=XrCTukcAFwsh&ttl=1563893021&t=53973ae23ade79cf83df980e340db2ee",
                    "bittorrent": "https://dl.humble.com/torrents/receiver_rc7_linux_32.tar.gz.torrent?gamekey=XrCTukcAFwsh&ttl=1563893021&t=a764f50c849e11fca433ded7293c29bd"
                },
                "timestamp": 1351193231,
                "human_size": "77.8 MB",
                "file_size": 81579646,
                "md5": "a1d857d9adf624954bafb8ff81f83e62"
                },
                {
                "sha1": "29e11bc500c61e4b9ac611c1f9098cffb9d23c66",
                "name": "64-bit .tar.gz (beta)",
                "url": {
                    "web": "https://dl.humble.com/receiver_rc7_linux_64.tar.gz?gamekey=XrCTukcAFwsh&ttl=1563893021&t=4933188f7368dd446289bbdd417c0109",
                    "bittorrent": "https://dl.humble.com/torrents/receiver_rc7_linux_64.tar.gz.torrent?gamekey=XrCTukcAFwsh&ttl=1563893021&t=35f84e0b31e4b203e8cc51131773bad5"
                },
                "timestamp": 1351193231,
                "human_size": "78.6 MB",
                "file_size": 82367293,
                "md5": "b9fc8987a1c8dfda65b6664f163bab7c"
                }
            ],
            "options_dict": {},
            "download_identifier": null,
            "android_app_only": false,
            "download_version_number": null
            },
            {
            "machine_name": "receiver_windows",
            "platform": "windows",
            "download_struct": [
                {
                "sha1": "2b41bbbe8274b6e046094a3dc6d78114d540feb5",
                "name": "Download",
                "url": {
                    "web": "https://dl.humble.com/receiver_rc7_win.zip?gamekey=XrCTukcAFwsh&ttl=1563893021&t=9c1a6bf812e279d06dcd82c4867cbd48",
                    "bittorrent": "https://dl.humble.com/torrents/receiver_rc7_win.zip.torrent?gamekey=XrCTukcAFwsh&ttl=1563893021&t=ef707cfa555b96a9744a27285db93116"
                },
                "timestamp": 1351130461,
                "human_size": "73.4 MB",
                "file_size": 76919992,
                "md5": "8c00fe1cd1f89d30778fe214b026a338"
                }
            ],
            "options_dict": {},
            "download_identifier": null,
            "android_app_only": false,
            "download_version_number": null
            }
        ],
        "library_family_name": null,
        "payee": {
            "human_name": "Wolfire Games",
            "machine_name": "wolfiregames"
        },
        "human_name": "Receiver",
        "custom_download_page_box_html": "",
        "icon": "https://hb.imgix.net/91f03ebaa8cdaca2cee6b2bd551b2e0807619c65.png?auto=format&s=f1073ba52415dc39c0211b71eda172f7"
        },
        {
        "machine_name": "lowlightcombat",
        "url": "http://www.wolfire.com/llc",
        "downloads": [
            {
            "machine_name": "lowlightcombat_windows",
            "platform": "windows",
            "download_struct": [
                {
                "sha1": "fd772de667f9ec9f922e230fe4f8bc7e61ec54bf",
                "name": "Download",
                "url": {
                    "web": "https://dl.humble.com/llc_win.zip?gamekey=XrCTukcAFwsh&ttl=1563893021&t=7d7ecf05acf1ae3f1abc4937d138ff16",
                    "bittorrent": "https://dl.humble.com/torrents/llc_win.zip.torrent?gamekey=XrCTukcAFwsh&ttl=1563893021&t=cf77cbbbc19c3ad06c0ae2eb1a9e4398"
                },
                "human_size": "42.7 MB",
                "file_size": 44815901,
                "md5": "90d41343ab339fc746780c02d5212f2d"
                }
            ],
            "options_dict": {},
            "download_identifier": "",
            "android_app_only": false,
            "download_version_number": null
            },
            {
            "machine_name": "lowlightcombat_linux",
            "platform": "linux",
            "download_struct": [
                {
                "human_size": "44 MB",
                "name": "32-bit",
                "url": {
                    "web": "https://dl.humble.com/llc_linux_32.zip?gamekey=XrCTukcAFwsh&ttl=1563893021&t=11f2d1f768659061dfa7fd0b07535a9d",
                    "bittorrent": "https://dl.humble.com/torrents/llc_linux_32.zip.torrent?gamekey=XrCTukcAFwsh&ttl=1563893021&t=efdf0c68c3cb6287423f4bbc927aaf51"
                },
                "sha1": "7e5252eb99cb6ce63942baba117fea1122118cfa",
                "file_size": 46144970,
                "md5": "c62dcd1f38c554b4a0ec90fe07ebdd8e"
                },
                {
                "human_size": "44.7 MB",
                "name": "64-bit",
                "url": {
                    "web": "https://dl.humble.com/llc_linux_64.zip?gamekey=XrCTukcAFwsh&ttl=1563893021&t=24bb6d55804aa26d4068c5b04910b513",
                    "bittorrent": "https://dl.humble.com/torrents/llc_linux_64.zip.torrent?gamekey=XrCTukcAFwsh&ttl=1563893021&t=c0d0c5c7ba275ab71a73d7a4ed7a9fb3"
                },
                "sha1": "fadab03f46ae899f1ea4e635c816b51f17f06bf7",
                "file_size": 46870317,
                "md5": "1dfab04a2db0bb88200bf10bc4ad054a"
                }
            ],
            "options_dict": {},
            "download_identifier": "",
            "android_app_only": false,
            "download_version_number": null
            },
            {
            "machine_name": "lowlightcombat_mac",
            "platform": "mac",
            "download_struct": [
                {
                "sha1": "bd207515200a182ce2ab19806e2ee88cdff1330a",
                "name": "Download",
                "url": {
                    "web": "https://dl.humble.com/llc_mac.zip?gamekey=XrCTukcAFwsh&ttl=1563893021&t=fc3ffec0cee68f6de32c6f501e7431e2",
                    "bittorrent": "https://dl.humble.com/torrents/llc_mac.zip.torrent?gamekey=XrCTukcAFwsh&ttl=1563893021&t=a86393d5c237342daefeb1c4b2b3c447"
                },
                "human_size": "43.8 MB",
                "file_size": 45921329,
                "md5": "3236351ca017a397188f74371720fc42"
                }
            ],
            "options_dict": {},
            "download_identifier": "",
            "android_app_only": false,
            "download_version_number": null
            }
        ],
        "library_family_name": null,
        "payee": {
            "human_name": "Wolfire Games",
            "machine_name": "wolfiregames"
        },
        "human_name": "Low Light Combat",
        "custom_download_page_box_html": null,
        "icon": "https://hb.imgix.net/8e0cc8822c2cb2e93f522481d7d5722bca9363c1.png?auto=format&s=ecca1cc40d5bd0155e6b279b3b85ab50"
        }
    ],
    "currency": null,
    "is_giftee": false,
    "claimed": true,
    "total": 29.95,
    "path_ids": [
        "33571110"
    ]
    }
'''
)
