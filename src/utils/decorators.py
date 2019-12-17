import asyncio
from contextlib import suppress
from typing import Callable


def double_click_effect(effect: Callable, timeout: float):
    """
    Decorator of asynchronious function that allows to call synchonious `effect` 
    if the function was called second time within `timeout` seconds
    """
    def _wrapper(fn):
        async def wrap(*args, **kwargs):
            async def delayed_fn():
                await asyncio.sleep(timeout)
                await fn(*args, **kwargs)

            if wrap.task is None or wrap.task.done() or wrap.task.cancelled():
                wrap.task = asyncio.create_task(delayed_fn())
                with suppress(asyncio.CancelledError):
                    await wrap.task
            else:
                wrap.task.cancel()
                return effect(*args, **kwargs)

        wrap.task = None
        return wrap
    return _wrapper