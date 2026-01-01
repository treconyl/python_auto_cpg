from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from typing import Callable


class QueueService:
    def __init__(self, max_workers: int = 5) -> None:
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    def submit(self, func: Callable[..., object], *args: object, **kwargs: object) -> Future:
        return self._executor.submit(func, *args, **kwargs)

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False)
