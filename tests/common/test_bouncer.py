from unittest import mock
import pytest
import asyncio

from plugin import bounce
from conftest import AsyncMock


@pytest.fixture
def mock_bouncer():
    def mock_callable(x): pass
    return mock.MagicMock(spec=mock_callable)


@pytest.fixture
def mock_async_fn():
    async def fn(): pass
    return AsyncMock(spec=fn)


@pytest.mark.asyncio
async def test_bouncer_called(mock_bouncer, mock_async_fn):
    decorated_fn = bounce(mock_bouncer, 1)(mock_async_fn)

    async def second_click():
        await asyncio.sleep(0.1)
        await decorated_fn()

    await asyncio.gather(decorated_fn(), second_click())

    assert mock_async_fn.call_count == 0
    assert mock_bouncer.assert_called_once()  # why this doesn't work
