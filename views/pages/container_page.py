from ago import human
from textual import work
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.reactive import reactive
from textual.widgets import Label, Link

from docker.api import get_container
from views.pages.page import Page


class ContainerPage(Page):

    DEFAULT_CSS = """
        ContainerPage {
            padding: 0 1;
            overflow-y: auto;
        
            #details-pane {
                layout: grid;
                height: auto;
                width: 1fr;
                grid-size: 2;
                grid-columns: auto 1fr;
            }
        }
        
    """

    status = reactive("")

    def __init__(self, container_name: str, container_id: str):
        super().__init__(title=f"Containers > {container_name} ({container_id[:12]})")
        self.container_id = container_id

    def compose(self) -> ComposeResult:
        with Container(id="details-pane"):
            yield Label("Status: ")
            yield Label("", id="status")
            yield Label("Ports: ")
            yield Vertical(id="ports")
            yield Label("Image: ")
            yield Label("", id="image")
            yield Label("Path: ")
            yield Label("", id="path")
            yield Label("Args: ")
            yield Label("", id="args")
            yield Label("Env: ")
            yield Label("", id="env")
            yield Label("Volumes: ")
            yield Label("", id="volumes")

    def on_mount(self) -> None:
        self.load_data()

    @work
    async def load_data(self) -> None:
        data = await get_container(id=self.container_id)
        self.query_one("#status", Label).update(f"{data.status} ({human(data.status_at, precision=1)})")
        await self.query_one("#ports", Vertical).mount(*[Link(f"{p[0]}/{p[1]}", url=f"http://localhost:{p[1]}") for p in data.ports])
        self.query_one("#image", Label).update(data.image)
        self.query_one("#path", Label).update(data.path)
        self.query_one("#args", Label).update("\n".join(data.args))
        self.query_one("#env", Label).update("\n".join(data.env))
        self.query_one("#volumes", Label).update("\n".join(data.volumes))

    def nav_back(self):
        from views.pages.containers_list_page import ContainersListPage
        self.nav_to(page=ContainersListPage())