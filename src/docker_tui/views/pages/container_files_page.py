from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

from rich.text import Text
from textual import work, on, events
from textual.app import ComposeResult
from textual.reactive import Reactive
from textual.widgets import DataTable, Label

from docker_tui.apis.docker_api import get_container_changes
from docker_tui.apis.models import ContainerFsChangeKind
from docker_tui.services.container_filesystem_explorer import list_container_files, FsEntry
from docker_tui.utils.formating import file_size, ago
from docker_tui.utils.input_helpers import TypeAhead
from docker_tui.views.components.responsive_table import ResponsiveTable, ColumnDefinition, Data, Row, Cell
from docker_tui.views.pages.page import Page


@dataclass
class FsViewModel:
    name: str
    path: str
    is_file: bool
    mode: str | None = None
    user: str | None = None
    group: str | None = None
    size: int = 0
    modified: datetime | None = None


class ContainerFilesPage(Page):
    DEFAULT_CSS = """
        #current-path-label{
            margin: 1;
            width: 1fr;
            dock: top;
            border-bottom: solid $secondary;
            text-style: bold;
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
                ColumnDefinition("tag", "Tag", "1fr", 2),
                ColumnDefinition("size", "Size", "1fr", 3),
                ColumnDefinition("modified", "Modified", "1fr", 4),
                ColumnDefinition("user", "User", "1fr", 5),
                ColumnDefinition("group", "Group", "1fr", 6),
            ]
        )
        self.changes: Dict[str, ContainerFsChangeKind] | None = None
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
            self.path = self._get_parent_path(self.path)
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

    @staticmethod
    def _get_parent_path(path: str):
        parent = path[:path.rindex("/")]
        return parent if parent != "" else "/"

    @work(exclusive=True)
    async def _populate_table(self, select_file: str = None):
        self.table.loading = True
        try:
            await self._fetch_changes_if_needed()
            entries = await list_container_files(container_id=self.container_id,
                                                 path=self.path)
            self.files = {e.path: e for e in entries}
        except Exception as ex:
            self.table.loading = False
            self.notify(title="Failed to list files", message=str(ex), severity="error")
            return

        view_models: List[FsViewModel] = []
        for entry in entries:
            view_models.append(FsViewModel(name=entry.name, path=entry.path, mode=entry.mode, user=entry.user,
                                           group=entry.group, size=entry.size, modified=entry.modified,
                                           is_file=entry.is_file))

        deleted_paths = [path
                         for path, kind in self.changes.items()
                         if self._get_parent_path(path) == self.path and kind == ContainerFsChangeKind.Deleted]
        for path in deleted_paths:
            view_models.append(FsViewModel(name=FsEntry.get_name(path=path), is_file=True, path=path))

        view_models = sorted(view_models, key=lambda e: e.name)

        data = Data(rows=[])
        for item in view_models:
            data.rows.append(Row(
                cells=[
                    Cell("mode", Text(item.mode or "---")),
                    Cell("name", Text(item.name)),
                    Cell("tag", self._get_tag(item)),
                    Cell("size", Text(file_size(item.size)) if item.is_file else Text("")),
                    Cell("modified", Text(ago(item.modified) if item.modified else "---")),
                    Cell("user", Text(item.user or "---")),
                    Cell("group", Text(item.group or "---"))
                ],
                row_key=item.path,
                selected=select_file == item.path
            ))
        self.table.update_table(data=data)
        self.table.loading = False

    def _get_tag(self, f: FsViewModel) -> Text:
        change = self.changes.get(f.path, None)
        if change == ContainerFsChangeKind.Added:
            return Text("Added", style="green")
        if change == ContainerFsChangeKind.Modified:
            return Text("Modified", style="dark_goldenrod")
        if change == ContainerFsChangeKind.Deleted:
            return Text("Deleted", style="red")

        return Text("")

    async def _fetch_changes_if_needed(self):
        if self.changes is None:
            changes = await get_container_changes(id=self.container_id)
            self.changes = {c.path: c.kind for c in changes}
