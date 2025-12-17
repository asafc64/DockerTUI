from abc import abstractmethod
from dataclasses import dataclass
from typing import List, TypeVar, Generic

from ago import human
from aiodocker import DockerError
from textual import on, work
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.css.query import NoMatches
from textual.dom import DOMNode
from textual.events import Key
from textual.message import Message
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import Input, ListView, Label, ListItem, ContentSwitcher, ProgressBar, Button

from docker_tui.apis.docker_api import pull_image
from docker_tui.apis.dockerhub_api import search_repo, search_tags
from docker_tui.apis.models import DockerHubRepo, DockerHubTag, PullingStatus
from docker_tui.views.components.debounced_input_handler import DebouncedInputHandler

SearchResultType = TypeVar("SearchResultType")


class StepPanel(Widget):
    def on_activated(self):
        ...

    def get_step_title(self) -> str:
        ...


class SearchPanel(Generic[SearchResultType], StepPanel):
    @dataclass
    class Selected(Message):
        caller: 'SearchPanel'
        selected_item: SearchResultType

        @property
        def control(self) -> DOMNode | None:
            return self.caller

    @dataclass
    class Canceled(Message):
        caller: 'SearchPanel'

        @property
        def control(self) -> DOMNode | None:
            return self.caller

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
    """

    def __init__(self, id: str, placeholder: str):
        super().__init__(id=id)
        self.input = Input(id="search-box", placeholder=placeholder)
        self.list_view = ListView(id="search-results")
        self.list_view.can_focus = False
        self.search_handler = None
        self.items: List[SearchResultType] = []

    def compose(self) -> ComposeResult:
        yield self.input
        yield self.list_view

    async def on_mount(self):
        self.search_handler = DebouncedInputHandler(input_widget=self.input, callback=self.search)

    def on_activated(self):
        self.input.focus()
        self.call_search()

    @work
    async def call_search(self):
        await self.search(text=self.input.value)

    async def search(self, text: str) -> None:
        self.list_view.loading = True

        self.items = await self.fetch_items(text=text)

        await self.list_view.clear()
        for item in self.items:
            await self.list_view.append(self.render_item(item))

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
            self.post_message(RepoSelectionStep.Selected(caller=self, selected_item=self.items[self.list_view.index]))
        if event.key == "escape":
            event.prevent_default()
            event.stop()
            self.post_message(RepoSelectionStep.Canceled(caller=self))

    @abstractmethod
    async def fetch_items(self, text: str) -> List[SearchResultType]:
        ...

    @abstractmethod
    def render_item(self, data: SearchResultType) -> ListItem:
        ...


class RepoSelectionStep(SearchPanel[DockerHubRepo]):
    DEFAULT_CSS = """
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

    def __init__(self, id: str):
        super().__init__(id=id, placeholder="Search image to pull...")

    def get_step_title(self) -> str:
        return "Step 1/3: Choose Image Repository"

    async def fetch_items(self, text: str) -> List[DockerHubRepo]:
        return await search_repo(query=text)

    def render_item(self, repo: DockerHubRepo) -> ListItem:
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

        return ListItem(row)


class TagSelectionStep(SearchPanel[DockerHubTag]):
    DEFAULT_CSS = """
        .row{
            width: 1fr;
            height: auto;
            layout: grid;
            grid-size: 2;
            grid-columns: 1fr auto;
            grid-gutter: 0 1;
        }
        .arc{
            column-span: 2;
            color: #888888;
            width: 1fr;
            text-wrap: wrap;
            text-overflow: fold;
        }
    """

    def __init__(self, id: str):
        super().__init__(id=id, placeholder="Search tag")
        self.repo = ""
        self.namespace = ""

    def get_step_title(self) -> str:
        return "Step 2/3: Choose Image Tag"

    async def fetch_items(self, text: str) -> List[DockerHubTag]:
        if not self.namespace or not self.repo:
            return []
        return await search_tags(namespace=self.namespace, repo=self.repo, query=text)

    def render_item(self, data: DockerHubTag) -> ListItem:
        row = Container(
            Label(data.name),
            Label(human(data.last_updated, precision=1, abbreviate=True)),
            Label(" · ".join([str(i) for i in data.images if str(i)]), classes="arc"),
            classes="row")
        return ListItem(row)


class LayerProgress(Widget):
    DEFAULT_CSS = """
        LayerProgress {
            width: 1fr; 
            height: 1;
            layout: grid;
            grid-size: 3;
            grid-columns: auto auto 1fr;
            grid-gutter: 0 1; 
        }
    """

    def __init__(self, id: str, layer_id: str, status: str):
        super().__init__(id=id)
        self.layer_id = layer_id
        self._status = Label(status, id="layer-status")
        self._progress_bar = ProgressBar(id="layer-progress", show_eta=False)

    def compose(self) -> ComposeResult:
        self._progress_bar.display = False
        yield Label(self.layer_id, id="layer-id")
        yield self._status
        yield self._progress_bar

    def update_progress(self, data: PullingStatus):
        self._status.update(data.status)
        if data.progress_detail \
                and data.progress_detail.total is not None \
                and data.progress_detail.current is not None:
            self._progress_bar.display = True
            self._progress_bar.update(total=data.progress_detail.total,
                                      progress=data.progress_detail.current)
        else:
            self._progress_bar.display = False


class PullingStep(StepPanel):
    class Done(Message):
        pass

    DEFAULT_CSS = """
        PullingStep{
            layout: grid;
            grid-rows: 1fr auto;
            background: $surface;
        }
        #layers-list{
            padding: 1;
            overflow-y: auto;
        }
        #ok-btn-wrapper {
            padding-bottom: 1;
            align: center middle;
            height: auto;
        }
        #ok-btn{
            width: auto;
        }
    """

    def __init__(self, id: str):
        super().__init__(id=id)
        self.container = Vertical(id="layers-list")
        self.ok_btn = Button("Ok", variant="success", id="ok-btn", disabled=True)
        self.repo = ""
        self.namespace = ""
        self.tag = ""

    def compose(self) -> ComposeResult:
        yield self.container
        with Container(id="ok-btn-wrapper"):
            yield self.ok_btn

    def get_step_title(self) -> str:
        return "Step 3/3: Pulling Image"

    def on_activated(self):
        self.start_pulling()

    @work
    async def start_pulling(self):
        self.container.loading = True
        try:
            async for item in pull_image(namespace=self.namespace, repo=self.repo, tag=self.tag):
                self.container.loading = False
                if item.id:
                    dom_id = f"Layer{item.id}"
                    try:
                        progress_bar: LayerProgress = self.query_one(f"#{dom_id}", expect_type=LayerProgress)
                    except NoMatches:
                        progress_bar = LayerProgress(id=dom_id, layer_id=item.id, status=item.status)
                        await self.container.mount(progress_bar)

                    progress_bar.update_progress(data=item)
            await self.container.mount(Label("Done!"))
            self.ok_btn.disabled = False
            self.ok_btn.focus()
        except DockerError as ex:
            self.notify(ex.message, title="Pulling Image Failed", severity="error")

    @on(Button.Pressed)
    def _on_ok(self):
        self.post_message(PullingStep.Done())


class DockerhubSearchModal(ModalScreen):
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
            #switcher > *{
                height: 1fr;
            }
        }
    """

    STEP_1_ID = "repo-step"
    STEP_2_ID = "tag-step"
    STEP_3_ID = "pull-step"

    def __init__(self):
        super().__init__()
        self._repo_step = RepoSelectionStep(id=self.STEP_1_ID)
        self._tag_step = TagSelectionStep(id=self.STEP_2_ID)
        self._pull_step = PullingStep(id=self.STEP_3_ID)
        self._header = Label(self._repo_step.get_step_title(), id="header")
        self._steps_switcher = ContentSwitcher(initial=self._repo_step.id, id="switcher")

    def compose(self) -> ComposeResult:
        with Container(id="body"):
            yield self._header
            with self._steps_switcher:
                yield self._repo_step
                yield self._tag_step
                yield self._pull_step

    def _show_step(self, step: StepPanel):
        self._steps_switcher.current = step.id
        self._header.update(step.get_step_title())
        step.on_activated()

    @on(SearchPanel.Selected, selector=f"#{STEP_1_ID}")
    def _on_repo_selected(self, message: SearchPanel.Selected):
        repo: DockerHubRepo = message.selected_item
        self._tag_step.namespace = repo.namespace
        self._tag_step.repo = repo.repo_name
        self._show_step(step=self._tag_step)

    @on(SearchPanel.Canceled, selector=f"#{STEP_1_ID}")
    def _on_repo_canceled(self):
        self.dismiss()

    @on(SearchPanel.Selected, selector=f"#{STEP_2_ID}")
    def _on_tag_selected(self, message: SearchPanel.Selected):
        tag: DockerHubTag = message.selected_item
        self._pull_step.namespace = self._tag_step.namespace
        self._pull_step.repo = self._tag_step.repo
        self._pull_step.tag = tag.name
        self._show_step(step=self._pull_step)

    @on(SearchPanel.Canceled, selector=f"#{STEP_2_ID}")
    def _on_tag_canceled(self):
        self._show_step(step=self._repo_step)

    @on(PullingStep.Done)
    def _on_pulling_done(self):
        self.dismiss()
