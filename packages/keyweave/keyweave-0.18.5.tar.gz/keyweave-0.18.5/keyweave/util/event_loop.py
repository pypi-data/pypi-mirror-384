# Add missing imports and logger
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading
import logging
from asyncio import AbstractEventLoop
from typing import Any, Callable, Coroutine

from keyweave.shorthand import SimpleCoroutine

logger = logging.getLogger("keyweave")


def create_event_loop(trace_name: str, workers: int = 1) -> AbstractEventLoop:

    loop = asyncio.new_event_loop()
    ready = threading.Event()
    pool = ThreadPoolExecutor(
        max_workers=workers, thread_name_prefix=f"{trace_name}"
    )

    def _run_loop() -> None:
        try:
            # Bind the loop to this thread
            asyncio.set_event_loop(loop)
            loop.set_default_executor(pool)
            # Set the executor while the loop is bound to the current thread
            # Signal that the loop/thread is ready
            ready.set()
            # Run the loop forever on this thread
            loop.run_forever()
        except Exception:
            logger.exception("Async loop crashed")

    t = threading.Thread(
        target=_run_loop, name=f"{trace_name}-loop", daemon=True
    )
    t.start()

    # Wait until the loop thread has bound the loop and set the executor
    ready.wait()
    return loop


def norm_maybe_async[**P, R](
    func: Callable[P, R | SimpleCoroutine[R]], /
) -> Callable[P, SimpleCoroutine[R]]:

    async def _wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
        result = func(*args, **kwargs)
        if isinstance(result, Coroutine):
            return await result  # type: ignore
        return result

    return _wrapped
