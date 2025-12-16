from rich.padding import PaddingDimensions
from rich.table import Table
from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.events import Key
from textual.screen import ModalScreen
from textual.widgets import OptionList, Input, ListView, Label, ListItem

from docker_tui.docker.api import search_dockerhub
from docker_tui.views.components.debounced_input_handler import DebouncedInputHandler


class DockerhubSearchModal(ModalScreen[str]):
    DEFAULT_CSS = """
        DockerhubSearchModal {
            align: center top;
            
            #search-box {
                border: none;
                padding: 1 2;
            }
            #search-results {
                border: none;
                padding: 0;
                padding-top: 1;
            }
            .search-result{
                width: 1fr;
                height: 2;
                margin: 0 1;
                layout: grid;
                grid-size: 2;
                grid-columns: 1fr auto;
                grid-gutter: 0 1;
            }
            .image-v-icon{
                color: $primary
            }
            .image-name{
                height: 1fr;
                text_overflow: ellipsis;
            }
            .image-description{
                column-span: 2;
                color: #888888;
                height: 1fr;
                text_overflow: ellipsis;
            }
            #body {
                margin: 3;
                width: 60;
                layout: grid;
                grid-size: 1;
                grid-rows: auto 1fr;
            }
        }
    """
    def __init__(self):
        super().__init__()
        self.input = Input(id="search-box", placeholder="Search image to pull...")
        # self.list_view = OptionList(id="search-results")
        # self.list_view.can_focus = False
        self.list_view = ListView(id="search-results")
        self.list_view.can_focus = False
        self.search_handler = None


    def compose(self) -> ComposeResult:
        with Container(id="body"):
            yield self.input
            yield self.list_view

    async def on_mount(self):
        self.search_handler = DebouncedInputHandler(input_widget=self.input, callback=self.search)

    async def search(self, text: str) -> None:
        self.list_view.loading = True
        images = await search_dockerhub(query=text)
        async with self.list_view.batch():
            await self.list_view.clear()
            for image in images:

                name = Label(image.name, classes="image-name")
                if image.is_official:
                    name = Horizontal(name, Label(" ✔", classes="image-v-icon"))

                icon = Label("✔" if image.is_official else " ", classes="image-icon")
                icon.tooltip = "Official image" if image.is_official else "Unofficial image"

                row = Container(
                    name,
                    Label(f"{image.stars}★"),
                    Label(image.description, classes="image-description"),
                    classes="search-result")

                await self.list_view.append(ListItem(row))
            self.list_view.index = 0
            self.list_view.loading = False

    def on_key(self, event: Key) -> None:
        if event.key == "down":
            self.list_view.index += 1
        if event.key == "up":
            self.list_view.index -= 1
        if event.key == "enter" and self.list_view.highlighted_option:
            option_id = self.list_view.highlighted_option.id
            event.prevent_default()
            event.stop()
            self.dismiss(option_id)
        if event.key == "escape":
            event.prevent_default()
            event.stop()
            self.dismiss(None)