import asyncio
from typing import Callable
from textual.widgets import Input
from textual.worker import Worker

SearchCallback = Callable[[str], Worker[None]]


class DebouncedInputHandler:
    def __init__(
        self,
        input_widget: Input,
        callback: SearchCallback,
        *,
        delay: float = 0.4):
        self.input = input_widget
        self.callback = callback
        self.delay = delay

        self._debounce_task: asyncio.Task | None = None

        self.input.watch(self.input, "value", self._on_change)

    def _on_change(self, value: str) -> None:
        if self._debounce_task:
            self._debounce_task.cancel()

        self._debounce_task = asyncio.create_task(
            self._debounced_call(value)
        )

    async def _debounced_call(self, value: str) -> None:
        try:
            await asyncio.sleep(self.delay)
            self.callback(value)
        except asyncio.CancelledError:
            pass
