import time
from dataclasses import dataclass


class MouseInputHelper:
    _last_click_time = 0

    @staticmethod
    def is_double_click() -> bool:
        now = time.time()
        last_one = MouseInputHelper._last_click_time
        MouseInputHelper._last_click_time = now
        return now - last_one <= 0.4


@dataclass
class TypeAheadResult:
    typed_keys: str
    is_repeated_single_key: bool


class TypeAhead:

    def __init__(self):
        self._type_buffer = ""
        self._last_key_time = None

    def register_key_press(self, key: str) -> TypeAheadResult:
        now = time.time()

        # reset buffer if more than 1/2 second passed
        if self._last_key_time and now - self._last_key_time > 0.5:
            self._type_buffer = ""

        self._last_key_time = now

        # handle cycling
        if self._type_buffer == key:
            return TypeAheadResult(typed_keys=self._type_buffer, is_repeated_single_key=True)

        self._type_buffer += key
        return TypeAheadResult(typed_keys=self._type_buffer, is_repeated_single_key=False)
