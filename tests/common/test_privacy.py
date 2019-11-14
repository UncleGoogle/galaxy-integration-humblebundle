import logging
from pytest import fixture

import privacy


@fixture
def sensitive_logger():
    logger = logging.getLogger()
    logger.setLevel('DEBUG')
    logger.addFilter(privacy.SensitiveFilter)
    yield logger


def test_strip_from_dict(sensitive_logger, caplog):
    sensitive_dict = {
        "name": 'this is ok',
        "redeemed_key_val": "top_secret"
    }
    logging.error(sensitive_dict)
    assert 'top_secret' not in caplog.text
