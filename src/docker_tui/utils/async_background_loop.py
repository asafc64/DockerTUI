import asyncio
import logging
from abc import abstractmethod

from docker_tui.utils.async_background import AsyncBackground

logger = logging.getLogger(__name__)

class AsyncBackgroundLoop(AsyncBackground):
    def __init__(self, delay: int = 1):
        super().__init__()
        self.delay = delay
        self._running = asyncio.Event()
        self._running.set()

    async def _run(self):
        try:
            while self._running.is_set():
                await self._run_in_loop()
                await asyncio.sleep(self.delay)
        except asyncio.CancelledError:
            logger.info("Loop cancelled.")
            raise
        except Exception as ex:
            print(ex)
            exit(1)

    @abstractmethod
    async def _run_in_loop(self):
        pass