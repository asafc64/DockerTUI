import asyncio
from typing import Callable, Awaitable

from textual.widgets import Input
from textual.worker import Worker

SearchCallback = Callable[[str], Awaitable[None]]


class DebouncedInputHandler:
    def __init__(
            self,
            input_widget: Input,
            callback: SearchCallback,
            *,
            delay: float = 0.4):

        self._input = input_widget
        self._callback = callback
        self._delay = delay
        self._worker: Worker[str] | None = None
        self._debounce_task: asyncio.Task | None = None
        self._input.watch(self._input, "value", self._on_change)

    def _on_change(self, value: str) -> None:
        if self._debounce_task:
            self._debounce_task.cancel()

        self._debounce_task = asyncio.create_task(
            self._debounce_and_run(value)
        )

    async def _debounce_and_run(self, value: str) -> None:
        try:
            await asyncio.sleep(self._delay)

            self._worker = self._input.run_worker(
                self._callback(value),
                group=f"debounced-call-{self._input.id}",
                exclusive=True,
            )

        except asyncio.CancelledError:
            pass
