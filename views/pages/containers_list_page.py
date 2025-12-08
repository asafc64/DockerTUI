import asyncio
from dataclasses import dataclass

from rich.text import Text
from textual import work, on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import DataTable, Label, Button

from docker.api import list_containers, stop_container, restart_container
from views.modals.action_verification_modal import ActionVerificationModal
from views.pages.page import Page




class ContainersListPage(Page):

    @dataclass
    class SelectedContainer:
        id: str
        name: str

    CSS = """
           DataTable {
               height: 1fr;
               overflow-y: auto;
               width: 100%;
           }
       """

    BINDINGS = [
        Binding("d", "show_details", "Show Details", group=Binding.Group("Actions")),
        Binding("l", "show_logs", "Show logs", group=Binding.Group("Actions")),
        Binding("f2", "stop", "Stop", group=Binding.Group("Actions")),
        Binding("f5", "restart", "Re/Start", group=Binding.Group("Actions")),
    ]

    is_root_page = True

    def __init__(self):
        super().__init__("Containers")
        self.table = DataTable(cursor_type='row')
        self.table.add_columns("", "Name", "Id", "Image", "Status")

    def compose(self) -> ComposeResult:
        yield self.table

    def on_mount(self) -> None:
        super().on_mount()
        self.table.loading = True
        self.load_data()

    @property
    def selected_container(self) -> SelectedContainer:
        row_key = list(self.table.rows.keys())[self.table.cursor_row].value
        id, name = row_key.split(";", 2)
        return ContainersListPage.SelectedContainer(id=id, name=name)

    def action_show_details(self):
        from views.pages.container_details_page import ContainerDetailsPage
        c = self.selected_container
        self.nav_to(page=ContainerDetailsPage(container_name=c.name, container_id=c.id))

    def action_show_logs(self):
        from views.pages.container_log_page import ContainerLogPage
        c = self.selected_container
        self.nav_to(page=ContainerLogPage(container_name=c.name, container_id=c.id))

    @work
    async def action_stop(self):
        #
        approved = await self.app.push_screen_wait(ActionVerificationModal(
            title=f"Are you sure you want to stop container '{self.selected_container.name}'?",
            button_text="Stop Container",
            button_variant="error"
        ))
        if not approved:
            return
        await stop_container(id=self.selected_container.id)
        self.load_data()

    @work
    async def action_restart(self):
        await restart_container(id=self.selected_container.id)
        self.load_data()

    @on(DataTable.RowSelected)
    def handle_row_selected(self, event: DataTable.RowSelected) -> None:
        from views.pages.container_details_page import ContainerDetailsPage
        c = self.selected_container
        self.nav_to(page=ContainerDetailsPage(container_name=c.name, container_id=c.id))

    @work
    async def load_data(self) -> None:
        self.table.loading = True
        containers = await list_containers()
        self.table.clear()
        for c in containers:
            row_key = f"{c.id};{c.name}"
            if c.state == 'exited':
                self.table.add_row(
                    Text('○', style="#888888"),
                    Text(c.name, style="#888888"),
                    Text(c.id[:12], style="#888888"),
                    Text(c.image, style="#888888"),
                    Text(c.status, style="#888888"),
                    key=row_key)
            else:
                self.table.add_row(
                    Text('●', style="green"),
                    Text(c.name),
                    Text(c.id[:12]),
                    Text(c.image),
                    Text(c.status),
                    key=row_key)
        self.table.loading = False
        self.table.focus()