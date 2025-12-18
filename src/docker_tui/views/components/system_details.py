from textual import work
from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label

from docker_tui.apis.docker_api import get_version


class SystemDetails(Widget):
    DEFAULT_CSS = """
        SystemDetails{
            layout: grid;
            grid-size: 2;
            grid-gutter: 0 1;
            grid-columns: auto auto;
            width: auto;
            height: auto;
            padding-right: 3;
        }
        .detail-name {
            width: auto;
            color: $text-accent;
        }
        .detail-value {
            width: auto;
            text-wrap: nowrap;
            text-overflow: ellipsis;
        }
    """
    LOADING = "<loading...>"

    docker_server = reactive(LOADING, recompose=True)
    docker_engine_version = reactive(LOADING, recompose=True)
    docker_api_version = reactive(LOADING, recompose=True)

    def compose(self) -> ComposeResult:
        yield Label("Server:", classes="detail-name")
        yield Label(self.docker_server, classes="detail-value").with_tooltip(self.docker_server)
        yield Label("Engine Version:", classes="detail-name")
        yield Label(self.docker_engine_version, classes="detail-value").with_tooltip(self.docker_engine_version)
        yield Label("Api Version:", classes="detail-name")
        yield Label(self.docker_api_version, classes="detail-value").with_tooltip(self.docker_api_version)

    def on_mount(self) -> None:
        self._refresh_details()
        self.set_interval(5, self._refresh_details)

    @work
    async def _refresh_details(self):
        try:
            version = await get_version()
            self.docker_server = version.server
            self.docker_engine_version = version.docker_engine_version
            self.docker_api_version = version.docker_api_version
        except:
            self.docker_server = "Offline"
            self.docker_engine_version = ""
            self.docker_api_version = ""
