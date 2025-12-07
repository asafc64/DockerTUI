from textual import work
from textual.app import ComposeResult
from textual.widgets import Log

from docker.api import get_container_logs
from views.pages.page import Page


class ContainerLogPage(Page):
    def __init__(self, container_name: str, container_id: str):
        super().__init__(title=f"Containers > {container_name} > Log")
        self.container_id = container_id

    def compose(self) -> ComposeResult:
        yield Log()

    def on_mount(self) -> None:
        super().on_mount()
        self.loading = True
        self.load_data()

    @work
    async def load_data(self) -> None:
        lines = await get_container_logs(id=self.container_id)
        log = self.query_one(Log)
        for line in lines:
            log.write_line(line)
        self.loading = False

    def nav_back(self):
        from views.pages.containers_list_page import ContainersListPage
        self.nav_to(page=ContainersListPage())