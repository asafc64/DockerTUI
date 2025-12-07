from rich.text import Text
from textual import work, on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import DataTable

from docker.api import list_containers
from views.pages.page import Page


class ContainersListPage(Page):

    CSS = """
           DataTable {
               height: 1fr;
               overflow-y: auto;
               width: 100%;
           }
       """

    BINDINGS = [
        Binding("d", "show_details", "Show Details", group=Binding.Group("Actions")),
        Binding("l", "show_logs", "Show logs", group=Binding.Group("Actions"))
    ]

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

    def get_selected_row_key(self) -> str:
        return list(self.table.rows.keys())[self.table.cursor_row].value

    def action_show_details(self):
        from views.pages.container_details_page import ContainerDetailsPage
        id, name = self.get_selected_row_key().split(";", 2)
        self.nav_to(page=ContainerDetailsPage(container_name=name, container_id=id))

    def action_show_logs(self):
        from views.pages.container_log_page import ContainerLogPage
        id, name = self.get_selected_row_key().split(";", 2)
        self.nav_to(page=ContainerLogPage(container_name=name, container_id=id))

    @on(DataTable.RowSelected)
    def handle_row_selected(self, event: DataTable.RowSelected) -> None:
        from views.pages.container_details_page import ContainerDetailsPage
        container_id, container_name = event.row_key.value.split(";", 2)
        self.nav_to(page=ContainerDetailsPage(container_name=container_name, container_id=container_id))

    @work
    async def load_data(self) -> None:
        self.table.loading = True
        containers = await list_containers()
        self.table.clear()
        for c in containers:
            row_key = f"{c.id};{c.name}"
            if c.state == 'exited':
                self.table.add_row(
                    Text('⭘', style="#888888"),
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