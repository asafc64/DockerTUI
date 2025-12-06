from rich.text import Text
from textual import work
from textual.app import ComposeResult
from textual.widgets import TabPane, DataTable, Tabs

from docker.api import list_containers


class ContainersListTabPane(TabPane):

    ID = "containers"

    CSS = """
           DataTable {
               height: 1fr;
               overflow-y: auto;
               width: 100%;
           }
       """

    def __init__(self):
        super().__init__("Containers", id=self.ID)
        self.table = DataTable(cursor_type='row')
        self.table.add_columns("", "Name", "Id", "Image", "Status")

    def compose(self) -> ComposeResult:
        yield self.table

    def on_mount(self) -> None:
        self.table.loading = True

    def on_tabbed_content_tab_activated(self, event: Tabs.TabActivated) -> None:
        """Called when a tab is activated."""
        if event.pane.id:
            pass

    @work
    async def load_data(self) -> None:
        self.table.loading = True
        containers = await list_containers()
        self.table.clear()
        for c in containers:
            if c.state == 'exited':
                self.table.add_row(
                    Text('⭘', style="#888888"),
                    Text(c.name, style="#888888"),
                    Text(c.id[:12], style="#888888"),
                    Text(c.image, style="#888888"),
                    Text(c.status, style="#888888"),
                    key=c.id)
            else:
                self.table.add_row(
                    Text('●', style="green"),
                    Text(c.name),
                    Text(c.id[:12]),
                    Text(c.image),
                    Text(c.status),
                    key=c.id)
        self.table.loading = False