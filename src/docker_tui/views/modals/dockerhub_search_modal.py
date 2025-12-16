from typing import List

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.events import Key
from textual.message import Message
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import Input, ListView, Label, ListItem

from docker_tui.apis.dockerhub_api import search_repo
from docker_tui.apis.models import DockerHubRepo
from docker_tui.views.components.debounced_input_handler import DebouncedInputHandler


class RepoSelectionStep(Widget):
    class Selected(Message):
        def __init__(self, repo: DockerHubRepo):
            super().__init__()
            self.selected_repo = repo

    class Canceled(Message):
        pass

    title = "Choose repo"

    DEFAULT_CSS = """
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
        .repo-v-icon{
            color: $primary
        }
        .repo-name{
            height: 1fr;
            text_overflow: ellipsis;
        }
        .repo-description{
            column-span: 2;
            color: #888888;
            height: 1fr;
            text_overflow: ellipsis;
        }
    """

    def __init__(self):
        super().__init__()
        self.input = Input(id="search-box", placeholder="Search image to pull...")
        self.list_view = ListView(id="search-results")
        self.list_view.can_focus = False
        self.search_handler = None
        self.repos: List[DockerHubRepo] = []

    def compose(self) -> ComposeResult:
        yield self.input
        yield self.list_view

    async def on_mount(self):
        self.search_handler = DebouncedInputHandler(input_widget=self.input, callback=self.search)

    async def search(self, text: str) -> None:
        self.list_view.loading = True
        self.repos = await search_repo(query=text)

        await self.list_view.clear()
        for repo in self.repos:

            name = Label(repo.display_name, classes="repo-name")
            if repo.is_official:
                name = Horizontal(name, Label(" ✔", classes="repo-v-icon"))

            icon = Label("✔" if repo.is_official else " ", classes="repo-icon")
            icon.tooltip = "Official repo" if repo.is_official else "Unofficial repo"

            row = Container(
                name,
                Label(f"{repo.stars}★"),
                Label(repo.description, classes="repo-description"),
                classes="search-result")

            await self.list_view.append(ListItem(row))
        self.list_view.index = 0
        self.list_view.loading = False

    def on_key(self, event: Key) -> None:
        if event.key == "down" and self.list_view.index is not None:
            self.list_view.index += 1
        if event.key == "up" and self.list_view.index is not None:
            self.list_view.index -= 1
        if event.key == "enter" and self.list_view.index is not None:
            event.prevent_default()
            event.stop()
            self.post_message(RepoSelectionStep.Selected(repo=self.repos[self.list_view.index]))
        if event.key == "escape":
            event.prevent_default()
            event.stop()
            self.post_message(RepoSelectionStep.Canceled())


class DockerhubSearchModal(ModalScreen[DockerHubRepo]):
    DEFAULT_CSS = """
        DockerhubSearchModal {
            align: center top;
            
            #body {
                margin: 3;
                width: 60;
                layout: grid;
                grid-size: 1;
                grid-rows: auto 1fr;
            }
            #header {
                width: 1fr;
                background: $panel;
                color: $foreground;
                height: 1;
                content-align: center middle;
            }
        }
    """

    def __init__(self):
        super().__init__()
        self.repo_selection_step = RepoSelectionStep()
        self.header = Label(id="header")
        self._set_step_title(1, self.repo_selection_step.title)

    def compose(self) -> ComposeResult:
        with Container(id="body"):
            yield self.header
            yield self.repo_selection_step

    def _set_step_title(self, step: int, title: str):
        self.header.update(f"Step {step}/3: {title}")

    @on(RepoSelectionStep.Selected)
    def _on_repo_selected(self, message: RepoSelectionStep.Selected):
        m = message.selected_repo
        pass
