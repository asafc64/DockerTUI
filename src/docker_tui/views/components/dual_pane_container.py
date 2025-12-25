from enum import Enum

from textual import events
from textual.app import ComposeResult
from textual.containers import Container
from textual.geometry import Size
from textual.reactive import Reactive
from textual.widget import Widget
from textual.widgets import Static


class PaneLayout(Enum):
    OnlyPrimary = 0
    Vertical = 1
    Horizontal = 2


class DualPaneContainer(Container):
    DEFAULT_CSS = """
        DualPaneContainer{
            & > *:last-child {
                padding-left: 1;
            }
            
            &.only-primary { 
                & > *:last-child {
                    height: 0;
                    min-height: 0;
                    overflow: hidden;
                }
                .pane-divider {
                    height: 0;
                    width: 0;
                    overflow: hidden;
                }
            }
            
            &.vertical {
                layout: grid;
                grid-rows: 1fr 1 1fr;
                
                .pane-divider {
                    width: 1fr;
                    border-top: solid $secondary;
                }
            }
            
            &.horizontal {
                layout: grid;
                grid-size: 3;
                grid-columns: 1fr 1 1fr;
                
                .pane-divider {
                    height: 1fr;
                    border-left: solid $secondary;
                }
            }
        }
    """

    active_layout: Reactive[PaneLayout] = Reactive(PaneLayout.OnlyPrimary)
    allowed_layouts: Reactive[tuple[PaneLayout, ...]] = Reactive((PaneLayout.OnlyPrimary,))

    def __init__(self, first: Widget, second: Widget):
        super().__init__()
        self._first = first
        self._second = second

    def compose(self) -> ComposeResult:
        yield self._first
        yield Static(classes="pane-divider")
        yield self._second

    def on_resize(self, event: events.Resize):
        self.call_later(self._recompute_allowed_layouts, event.size)

    def toggle_pages_layout(self):
        current_idx = self.allowed_layouts.index(self.active_layout)
        next_idx = (current_idx + 1) % len(self.allowed_layouts)
        self.active_layout = self.allowed_layouts[next_idx]

        if len(self.allowed_layouts) == 1:
            self.notify("Screen too small - only the main layout is allowed.",
                        title="Failed to toggle layout",
                        severity="warning")

    def watch_active_layout(self, value: PaneLayout):
        self.set_class(value == PaneLayout.OnlyPrimary, "only-primary")
        self.set_class(value == PaneLayout.Vertical, "vertical")
        self.set_class(value == PaneLayout.Horizontal, "horizontal")

    def watch_allowed_layouts(self, layouts: tuple[PaneLayout, ...]) -> None:
        if self.active_layout not in layouts:
            self.active_layout = layouts[0]

    def _recompute_allowed_layouts(self, size: Size) -> None:
        layouts = [PaneLayout.OnlyPrimary]

        ratio = size.width / size.height

        if ratio > 1.5:
            layouts.append(PaneLayout.Horizontal)

        if 1 / ratio > 0.15:
            layouts.append(PaneLayout.Vertical)

        layouts_tuple = tuple(layouts)

        if layouts_tuple == self.allowed_layouts:
            return  # critical: no churn

        self.allowed_layouts = layouts_tuple
