from asyncio import AbstractEventLoop, Future
from typing import Any, Coroutine, Protocol
from dataclasses import dataclass, field

from keyweave.shorthand import SimpleCoroutine
from keyweave.util.event_loop import create_event_loop, norm_maybe_async


class ScheduleItem(Protocol):
    def __call__(self) -> None | SimpleCoroutine[None]: ...


class Scheduler(Protocol):

    def __call__(self, func: ScheduleItem, /) -> None: ...


class ScheduleErrorHandler(Protocol):
    def __call__(self, error: BaseException, /) -> None: ...


@dataclass(kw_only=True)
class AsyncIoScheduler(Scheduler):
    on_error: ScheduleErrorHandler
    workers: int
    _event_loop: AbstractEventLoop = field(init=False)

    def __post_init__(self):
        self._event_loop = create_event_loop(
            "KeyWeave-Scheduler", workers=self.workers
        )

    def __call__(self, func: ScheduleItem) -> None:
        def callback(future: Future[None]):
            ex = future.exception()
            if ex:
                self.on_error(ex)

        def run_item():
            self._event_loop.create_task(
                norm_maybe_async(func)()
            ).add_done_callback(callback)

        self._event_loop.call_soon_threadsafe(run_item)


def default_scheduler(on_error: ScheduleErrorHandler):
    return AsyncIoScheduler(workers=1, on_error=on_error)
