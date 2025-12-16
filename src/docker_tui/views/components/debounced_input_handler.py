import asyncio
from typing import Awaitable, Callable
from textual.widgets import Input

SearchCallback = Callable[[str], Awaitable[None]]


class DebouncedInputHandler:
    def __init__(
        self,
        input_widget: Input,
        callback: SearchCallback,
        *,
        delay: float = 0.4,
    ) -> None:
        self.input = input_widget
        self.callback = callback
        self.delay = delay

        self._debounce_task: asyncio.Task | None = None
        self._active_task: asyncio.Task | None = None

        self.input.watch(self.input, "value", self._on_change)

    def _on_change(self, value: str) -> None:
        if self._debounce_task:
            self._debounce_task.cancel()

        if self._active_task:
            self._active_task.cancel()

        self._debounce_task = asyncio.create_task(
            self._debounced_call(value)
        )

    async def _debounced_call(self, value: str) -> None:
        try:
            await asyncio.sleep(self.delay)
            self._active_task = asyncio.create_task(
                self.callback(value)
            )
            await self._active_task
        except asyncio.CancelledError:
            pass
