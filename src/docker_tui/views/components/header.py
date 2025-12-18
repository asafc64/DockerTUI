from textual.app import ComposeResult
from textual.widget import Widget

from docker_tui.views.components.shortcuts import Shortcuts
from docker_tui.views.components.system_details import SystemDetails


class Header(Widget):
    DEFAULT_CSS = """
        Header{
            dock: top;
            width: auto;
            height: auto;
            layout: horizontal;
        }
    """

    def compose(self) -> ComposeResult:
        yield SystemDetails()
        yield Shortcuts()
