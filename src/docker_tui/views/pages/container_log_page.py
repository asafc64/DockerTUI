from textual.app import ComposeResult

from docker_tui.views.components.containers_log import ContainersLog
from docker_tui.views.pages.page import Page


class ContainerLogPage(Page):
    def __init__(self, container_name: str, container_id: str):
        super().__init__(title=f"Containers > {container_name} > Log")
        self.container_id = container_id

    def compose(self) -> ComposeResult:
        yield ContainersLog(container_ids=[self.container_id])

    def nav_back(self):
        from docker_tui.views.pages.containers_list_page import ContainersListPage
        self.nav_to(page=ContainersListPage())
