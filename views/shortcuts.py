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

        # Group multiple shortcut with the same action
        actions = {}
        for b in bindings:
            action_key = b.description
            actions.setdefault(action_key, []).append(b.key_display or b.key)

        self.styles.height = 1 +len(actions)
        self.title = title
        self.actions = actions

    def compose(self) -> ComposeResult:
        yield Label(self.title, classes="title")
        for (description, hotkeys) in self.actions.items():
            yield Label(",".join([f"<{k}>" for k in hotkeys]), classes="binding-key")
            yield Label(description)

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

