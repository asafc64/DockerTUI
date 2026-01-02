from dataclasses import dataclass
from typing import List

from textual import events, on
from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import ListView, ListItem, Label


@dataclass
class MenuItem:
    action: str
    label: str
    hot_key: str


class MenuModal(ModalScreen[str]):
    DEFAULT_CSS = """
        MenuModal {
            align: center middle;
        }
        #body {
            width: 0.3fr;
            height: auto;
            background: $surface;
        }
        .item-content {
            layout: grid;
            height: 1;
            grid-size: 2;
            grid-columns: auto 1fr;
            
            & > .item-key {
                color: $footer-key-foreground;
                text-style: bold;
                padding-right: 1;
            }
        }
        
        #menu-items-list {
            background: transparent;
            height: auto;
            width: auto;
            padding: 1 2;
            
            & > ListItem {
                border: round $foreground 25%;
                padding-left: 1;
                
                &.-hovered {
                    border: round $border 50%;
                    background: transparent;
                }
                &.-highlight {
                    border: round $border;
                    background: transparent;
                }
            }
        }
        
    """

    def __init__(self, items: List[MenuItem]):
        super().__init__()
        self._items = items

    def compose(self) -> ComposeResult:
        with Container(id="body"):
            yield ListView(
                *[ListItem(self._get_item_widget(item)) for item in self._items],
                id="menu-items-list"
            )

    @on(ListView.Selected)
    def on_item_selected(self, msg: ListView.Selected):
        item = self._items[msg.index]
        self.dismiss(item.action)

    def on_key(self, event: events.Key):
        if event.key == "escape":
            event.prevent_default()
            event.stop()
            self.dismiss(None)

        if event.character:
            item = next((i for i in self._items if i.hot_key.lower() == event.character.lower()), None)
            if item:
                self.dismiss(item.action)

    def on_click(self, event: events.Click) -> None:
        if not self.query_one("#body").region.contains(event.screen_x, event.screen_y):
            self.dismiss()

    @staticmethod
    def _get_item_widget(item: MenuItem) -> Widget:
        return Container(
            Label(item.hot_key, classes="item-key"),
            Label(item.label, classes="item-label"),
            classes="item-content"
        )
