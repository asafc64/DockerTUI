import time


class DoubleClickDetector:
    _last_click_time = 0

    @staticmethod
    def is_double_click() -> bool:
        now = time.time()
        last_one = DoubleClickDetector._last_click_time
        DoubleClickDetector._last_click_time = now
        return now - last_one <= 0.4


class TypeToSelect:

    def __init__(self):
        self._type_buffer = ""
        self._last_key_time = None

    def force_reset(self):
        self._type_buffer = ""
        self._last_key_time = None

    def register_key_press(self, key: str) -> str:
        now = time.time()

        # reset buffer if more than 1/2 second passed
        if self._last_key_time and now - self._last_key_time > 0.5:
            self._type_buffer = ""

        self._last_key_time = now

        # handle cycling
        if self._type_buffer != key:
            self._type_buffer += key

        return self._type_buffer

    def get_sequence(self) -> str:
        now = time.time()
        return "" if self._last_key_time and now - self._last_key_time > 0.5 else self._type_buffer
