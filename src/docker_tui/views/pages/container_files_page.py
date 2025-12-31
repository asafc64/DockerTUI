from typing import Dict

from rich.text import Text
from textual import work, on, events
from textual.app import ComposeResult
from textual.reactive import Reactive
from textual.widgets import DataTable, Label

from docker_tui.services.container_filesystem_explorer import list_container_files, FsEntry
from docker_tui.utils.formating import file_size, ago
from docker_tui.utils.input_helpers import TypeAhead
from docker_tui.views.components.responsive_table import ResponsiveTable, ColumnDefinition, Data, Row, Cell
from docker_tui.views.pages.page import Page


class ContainerFilesPage(Page):
    DEFAULT_CSS = """
        #current-path-label{
            margin: 1;
            width: 1fr;
            dock: top;
            border-bottom: solid $secondary;
        }
    """

    path: Reactive[str] = Reactive("/")

    def __init__(self, container_name: str, container_id: str):
        super().__init__(title=f"Containers > {container_name} > Files")
        self.container_id = container_id
        self.path_label = Label("/", id="current-path-label")
        self.table = ResponsiveTable(
            id="files-table",
            columns=[
                ColumnDefinition("mode", "Mode", "11", 1),
                ColumnDefinition("name", "Name", "3fr", 0, min_width=50),
                ColumnDefinition("size", "Size", "1fr", 2),
                ColumnDefinition("modified", "Modified", "1fr", 3),
                ColumnDefinition("user", "User", "1fr", 4),
                ColumnDefinition("group", "Group", "1fr", 5),
            ]
        )
        self.files: Dict[str, FsEntry] = {}
        self.type_ahead = TypeAhead()

    def compose(self) -> ComposeResult:
        yield self.path_label
        yield self.table

    def on_mount(self) -> None:
        self.table.loading = True
        self._populate_table()

    def nav_back(self):
        from docker_tui.views.pages.containers_list_page import ContainersListPage
        self.nav_to(page=ContainersListPage())

    @on(DataTable.RowSelected)
    def handle_row_selected(self, event: DataTable.RowSelected) -> None:
        file = self.files[event.row_key.value]
        if file.is_directory:
            self.path = file.path

    def watch_path(self, old_value: str, new_value: str):
        self.path_label.update(new_value)
        self._populate_table(select_file=old_value)

    def _on_key(self, event: events.Key) -> None:
        if (event.key == "escape" or event.key == "backspace") and not self._is_root():
            self.path = self._get_parent_path()
            event.prevent_default()
            event.stop()
            return

        if event.character:
            result = self.type_ahead.register_key_press(key=event.character)

            items = list(self.files.values())
            from_idx = self.table.get_selected_row_index() + 1
            ordered_items = items[from_idx:] + items[:from_idx]

            next_match = next((f.path for f in ordered_items if f.name.startswith(result.typed_keys)), None)
            if next_match:
                self.table.select_row(row_key=next_match)

    def _is_root(self):
        return self.path == "/"

    def _get_parent_path(self):
        return self.path[:self.path.rindex("/")]

    @work(exclusive=True)
    async def _populate_table(self, select_file: str = None):
        self.table.loading = True
        try:
            entries = await list_container_files(container_id=self.container_id,
                                                 path=self.path + "/*")
            self.files = {e.path: e for e in entries}
        except Exception as ex:
            self.table.loading = False
            self.notify(title="Failed to list files", message=str(ex), severity="error")
            return

        data = Data(rows=[])
        for entry in entries:
            data.rows.append(Row(
                cells=[
                    Cell("mode", Text(entry.mode)),
                    Cell("name", Text(entry.name)),
                    Cell("size", Text(file_size(entry.size)) if entry.is_file else Text("")),
                    Cell("modified", Text(ago(entry.modified))),
                    Cell("user", Text(entry.user)),
                    Cell("group", Text(entry.group))
                ],
                row_key=entry.path,
                selected=select_file == entry.path
            ))
        self.table.update_table(data=data)
        self.table.loading = False
