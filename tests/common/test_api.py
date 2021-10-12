from unittest.mock import patch
from webservice import AuthorizedHumbleAPI

from galaxy.api.errors import BackendError
from galaxy.unittest.mock import async_raise
import pytest


@pytest.fixture
def client_session():
    with patch("aiohttp.ClientSession") as mock:
        yield mock.return_value


def test_filename_from_web_link():
    web_link = 'https://dl.humble.com/Almost_There_Windows.zip?gamekey=AbR9TcsD4ecueNGw&ttl=1587335864&t=a04a9b4f6512b7958f6357cb7b628452'
    expected = 'Almost_There_Windows.zip'
    assert expected == AuthorizedHumbleAPI._filename_from_web_link(web_link)


@pytest.mark.asyncio
async def test_handle_exception(client_session):
    client_session.request.return_value = async_raise(BackendError)
    with pytest.raises(BackendError):
        await AuthorizedHumbleAPI()._get_webpack_data("mock_path", "mock_webpack_id")