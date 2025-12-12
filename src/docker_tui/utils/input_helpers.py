import time


class MouseInputHelper:

    _last_click_time = 0

    @staticmethod
    def is_double_click() -> bool:
        now = time.time()
        last_one = MouseInputHelper._last_click_time
        MouseInputHelper._last_click_time = now
        return now - last_one <= 0.4