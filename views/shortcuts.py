from itertools import groupby
from typing import List

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Grid, Container, Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Label, Rule

class ShortcutsGrid(Widget):
    DEFAULT_CSS = """
        ShortcutsGrid {
            layout: grid;
            height: auto;
            width: 1fr;
            grid-size: 2;
            grid-columns: auto 1fr;
            
            .title{
                column-span: 2;
                text-style: underline;
            }
            
            .binding-key {
                color: $footer-key-foreground;
                text-style: bold;
                padding-right: 1;
            }
        }
    """
    def __init__(self, title: str, bindings: List[Binding]):
        super().__init__()
        self.styles.height = 1 +len(bindings)
        self.title = title
        self.bindings = bindings

    def compose(self) -> ComposeResult:
        yield Label(self.title, classes="title")
        for b in self.bindings:
            yield Label(f"<{b.key}>", classes="binding-key")
            yield Label(f"{b.description}")

class Shortcuts(Horizontal):
    BORDER_TITLE = "Hello Widget"
    DEFAULT_CSS = """
        Shortcuts{
            dock: top;
            layout: horizontal;
            width: 100%;
            height: auto;
            # background: $panel;
            color: $foreground;
        }
        .nav {
             background: red;
             max-width: 40;
        }
        
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        groups = {}

        for b in self.screen.active_bindings.values():
            group_name = b.binding.group.description if b.binding.group else "System"
            groups.setdefault(group_name, []).append(b.binding)

        for (g, bs) in groups.items():
            yield ShortcutsGrid(g, list(bs))

