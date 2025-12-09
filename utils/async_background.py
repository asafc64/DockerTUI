import asyncio
from abc import ABC, abstractmethod


class AsyncBackground(ABC):
    def __init__(self):
        self._task = None

    def start(self):
        if self.is_running():
            return

        self._task = asyncio.create_task(self._run())

    async def close(self):
        if self._task is None:
            return

        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        finally:
            self._task = None

    def is_running(self):
        return self._task is not None and not self._task.done()

    @abstractmethod
    async def _run(self):
        pass
