from ago import human
from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.widgets import Label, Link

from docker_tui.apis.docker_api import get_container_details
from docker_tui.views.components.container_cpu_usage_plot import ContainerCpuUsagePlot
from docker_tui.views.components.container_memory_usage_plot import ContainerMemoryUsagePlot
from docker_tui.views.pages.page import Page


class ContainerDetailsPage(Page):
    DEFAULT_CSS = """
        ContainerDetailsPage {

            layout: horizontal;
            padding: 0 1;
            overflow-y: scroll;
          
            #details-pane {
                layout: grid;
                height: auto;
                width: 1fr;
                grid-size: 2;
                grid-columns: auto 1fr;
                grid-gutter: 1;
            }
            
            #plots-host {
                width: 1fr;
                height: auto;
            }
            
            .stat-plot{
                height: 12;
                margin: 0 1 1 1 ;
            }
        }
    """

    BINDINGS = [
        Binding("up", "scroll_up", "Scroll Up", group=Binding.Group("Browse")),
        Binding("down", "scroll_down", "Scroll Down", group=Binding.Group("Browse")),
    ]

    def action_scroll_up(self):
        self.scroll_up()

    def action_scroll_down(self):
        self.scroll_down()

    def __init__(self, container_name: str, container_id: str):
        super().__init__(title=f"Containers > {container_name}")
        self.container_name = container_name
        self.container_id = container_id
        self.details_panel = Container(id="details-pane")

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
        with Vertical(id="plots-host"):
            yield ContainerCpuUsagePlot(container_id=self.container_id, classes="stat-plot")
            yield ContainerMemoryUsagePlot(container_id=self.container_id, classes="stat-plot")

    def on_mount(self) -> None:
        super().on_mount()
        self.loading = True
        self.load_data()

    @work
    async def load_data(self) -> None:
        data = await get_container_details(id=self.container_id)
        self.query_one("#status", Label).update(f"{data.status} ({human(data.status_at, precision=1)})")
        await self.query_one("#ports", Vertical).mount(
            *[Link(f"{p[0]}/{p[1]}", url=f"http://localhost:{p[1]}") for p in data.ports])
        self.query_one("#image", Label).update(data.image)
        self.query_one("#path", Label).update(data.path)
        self.query_one("#args", Label).update("\n".join(data.args))
        self.query_one("#env", Label).update("\n".join(data.env))
        self.query_one("#volumes", Label).update("\n".join(data.volumes))
        self.loading = False
        self.focus()

    def nav_back(self):
        from docker_tui.views.pages.containers_list_page import ContainersListPage
        self.nav_to(page=ContainersListPage())
