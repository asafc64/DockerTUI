from rich.text import Text
from textual import work, on
from textual.app import ComposeResult
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

    def __init__(self):
        super().__init__("Containers")
        self.table = DataTable(cursor_type='row')
        self.table.add_columns("", "Name", "Id", "Image", "Status")

    def compose(self) -> ComposeResult:
        yield self.table

    def on_mount(self) -> None:
        self.table.loading = True
        self.load_data()

    @on(DataTable.RowSelected)
    def handle_row_selected(self, event: DataTable.RowSelected) -> None:
        from views.pages.container_page import ContainerPage
        container_id, container_name = event.row_key.value.split(";", 2)
        self.nav_to(page=ContainerPage(container_name=container_name, container_id=container_id))

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