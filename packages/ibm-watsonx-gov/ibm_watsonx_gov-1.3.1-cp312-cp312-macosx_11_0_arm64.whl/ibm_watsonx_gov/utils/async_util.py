# ----------------------------------------------------------------------------------------------------
# IBM Confidential
# Licensed Materials - Property of IBM
# 5737-H76, 5900-A3Q
# © Copyright IBM Corp. 2025  All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or disclosure restricted by
# GSA ADPSchedule Contract with IBM Corp.
# ----------------------------------------------------------------------------------------------------


import asyncio
from typing import Any, Awaitable, Iterable


def run_in_event_loop(task, *args, **kwargs):
    """Run the given async task in an event loop, safely handling loop reuse."""
    try:
        event_loop = asyncio.get_running_loop()
        # Use existing event loop and wait for the task to be executed.
        import nest_asyncio
        nest_asyncio.apply()
        return event_loop.run_until_complete(task(*args, **kwargs))
    except RuntimeError:
        # No running loop, create one and close it when done
        event_loop = asyncio.new_event_loop()
        try:
            return event_loop.run_until_complete(task(*args, **kwargs))
        finally:
            event_loop.close()


async def gather_with_concurrency(
    coros: Iterable[Awaitable],
    return_exceptions: bool = False,
    max_concurrency: int = 10,
) -> Any:
    semaphore = asyncio.Semaphore(max_concurrency)

    async def safe_coroutine_fn(fn):
        async with semaphore:
            return await fn

    tasks = [asyncio.create_task(safe_coroutine_fn(fn)) for fn in coros]
    try:
        return await asyncio.gather(*tasks, return_exceptions=return_exceptions)
    except Exception as ex:
        for task in tasks:
            task.cancel()
        raise ex


def start_event_loop_run_func(func, data):
    """
    Create a wrapper function to start the event loop in the thread as unitxt LiteLLMInference fails without it.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return func(data)
    finally:
        loop.close()
        asyncio.set_event_loop(None)
