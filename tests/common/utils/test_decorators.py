from unittest import mock
import pytest
import asyncio

from utils.decorators import double_click_effect
from conftest import AsyncMock


@pytest.fixture
def mock_dbclick():
    def mock_callable(x): pass
    return mock.MagicMock(spec=mock_callable)


@pytest.fixture
def mock_async_fn():
    return AsyncMock()


@pytest.fixture
def delayed_fn():
    async def fn(delay, awaitable, *args, **kwargs):
        await asyncio.sleep(delay)
        await awaitable(*args, **kwargs)
    return fn


@pytest.mark.asyncio
async def test_clicked_once(mock_dbclick, mock_async_fn):
    timeout = 0.1
    decorated_fn = double_click_effect(timeout, mock_dbclick)(mock_async_fn)
    await decorated_fn()
    assert mock_async_fn.call_count == 1
    assert mock_dbclick.call_count == 0


@pytest.mark.asyncio
async def test_fast_double_click(mock_dbclick, mock_async_fn):
    timeout = 0.1
    decorated_fn = double_click_effect(timeout, mock_dbclick)(mock_async_fn)
    await asyncio.gather(decorated_fn(), decorated_fn())
    assert mock_async_fn.call_count == 0
    assert mock_dbclick.call_count == 1


@pytest.mark.asyncio
async def test_slow_double_click(mock_dbclick, mock_async_fn, delayed_fn):
    timeout = 0.1
    decorated_fn = double_click_effect(timeout, mock_dbclick)(mock_async_fn)
    await asyncio.gather(
        decorated_fn(),
        delayed_fn(timeout + 0.1, decorated_fn)
    )
    assert mock_async_fn.call_count == 2
    assert mock_dbclick.call_count == 0


@pytest.mark.asyncio
async def test_fast_triple_click(mock_dbclick, mock_async_fn, delayed_fn):
    timeout = 0.1
    decorated_fn = double_click_effect(timeout, mock_dbclick)(mock_async_fn)
    await asyncio.gather(
        decorated_fn(),
        delayed_fn(0.01, decorated_fn),
        delayed_fn(0.02, decorated_fn)
    )
    assert mock_async_fn.call_count == 1
    assert mock_dbclick.call_count == 1
