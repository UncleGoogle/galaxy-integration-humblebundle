import logging
import pytest
from model.game import Key

import privacy


@pytest.fixture
def sensitive_logger():
    logger = logging.getLogger()
    logger.setLevel('DEBUG')
    logger.addFilter(privacy.SensitiveFilter())
    yield logger


def test_strip_from_dict(sensitive_logger, caplog):
    sensitive_dict = {
        "name": 'this is ok',
        "redeemed_key_val": "TOP_SECRET"
    }
    logging.error(sensitive_dict)
    assert "TOP_SECRET" not in caplog.text


def test_strip_from_key(sensitive_logger, caplog):
    key_val = "ABCD-EDGH-IJKL"
    data = {
        "machine_name": "dead_space_origin_key",
        "human_name": "Dead Space Origin Key",
        "redeemed_key_val": key_val
    }
    key = Key(data)
    logging.error(key)
    assert key_val not in caplog.text
    assert key.key_val == key_val  # logger doesnt affect actual data


def test_strip_extra(sensitive_logger, caplog):
    """Extra arguments are used also by sentry.io"""
    key_val = "ABCD-EDGH-IJKL"
    data = {
        "machine_name": "dead_space_origin_key",
        "human_name": "Dead Space Origin Key",
        "redeemed_key_val": key_val
    }
    logging.error("some text", extra=data)
    assert key_val not in caplog.text
    for record in caplog.records:
        if hasattr(record, "redeemed_key_val"):
            assert record.redeemed_key_val == '***'
    assert data['redeemed_key_val'] == key_val  # logger doesnt affect actual data

def test_strip_extra_game_key(sensitive_logger, caplog):
    """Extra arguments are used also by sentry.io"""
    key_val = "ABCD-EDGH-IJKL"
    data = {
        "machine_name": "dead_space_origin_key",
        "human_name": "Dead Space Origin Key",
        "redeemed_key_val": key_val
    }
    key = Key(data)
    logging.error("some text", extra={'game': key})
    for record in caplog.records:
        if hasattr(record, "game"):
            assert record.game.key_val != key_val
            assert record.game._data['redeemed_key_val'] != key_val
    # logger doesnt affect actual data
    assert key._data['redeemed_key_val'] == key_val
    assert key.key_val == key_val


@pytest.mark.parametrize("key_val", [
    "DF4F-22JFD-GIV8",
    "DF4FS-22JFD-GIV84",
    "ABCD-1EFG-HIJK-2LMN",
    "HB44-J2BY-S8VA-PWCW-5WT4",
    "ABCDE-FGHJK-LMNOP-QRSTU-VWXYZ",
    "H44-JBY-SVA-PCW-5T4-543-555-BDL",
    "DFS-22FD-GI4DDAAL-F9F-SDFL",
    "asdf32-adfl23f2-s333",
    "DF4FS-22JFD-GIV84,",
    " DF4FS-22JFD-GIV84\n",
    'key_val="DF4FS-22JFD-GIV84"',
])
def test_strip_from_str(sensitive_logger, caplog, key_val):
    msg = f'DATA {key_val} other things'
    logging.error(msg)
    assert "other things" in caplog.text
    assert key_val not in caplog.text


@pytest.mark.parametrize("key_val", [
    "totally not a key",
    "redeemend_key_val",
    "TWO-WORDS",
    "2FAJH_DWDDS_234KL",
])
def test_strip_from_str_false_positives(sensitive_logger, caplog, key_val):
    msg = f'DATA {key_val} other things'
    logging.error(msg)
    assert key_val in caplog.text

